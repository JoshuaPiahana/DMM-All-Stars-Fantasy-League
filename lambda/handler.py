"""
Lambda entry point — polls OSRS tournament hiscores and forwards to App Runner.

Invocation flow (triggered by EventBridge Scheduler every 15 min):
  1. GET  {APP_RUNNER_URL}/internal/players  → list of {id, account_name} to fetch
  2. Fetch tournament hiscores for each player with a known account_name
  3. POST {APP_RUNNER_URL}/internal/poll     → App Runner writes snapshots to RDS

Both internal endpoints require the INGEST_SECRET header.
Lambda is intentionally NOT in the VPC so it has direct internet access to OSRS.
App Runner (which is in the VPC) handles all DB writes.
"""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.parse
import urllib.request

import boto3
from scraper import TOURNAMENT_URL, fetch_player

log = logging.getLogger()
log.setLevel(logging.INFO)

_secret_cache: str | None = None


def _get_ingest_secret() -> str:
    global _secret_cache
    if _secret_cache:
        return _secret_cache
    client = boto3.client("secretsmanager")
    resp = client.get_secret_value(SecretId=os.environ["INGEST_SECRET_ARN"])
    _secret_cache = resp["SecretString"]
    return _secret_cache


def _get_players(app_url: str, secret: str) -> list[dict]:
    """Fetch the list of active players (with account names) from App Runner."""
    url = f"{app_url}/internal/players"
    req = urllib.request.Request(url, headers={"X-Ingest-Secret": secret})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.URLError as exc:
        log.error("Failed to fetch player list: %s", exc)
        return []


def _post_ingest(app_url: str, secret: str, payload: dict) -> None:
    """POST snapshot data to App Runner's ingest endpoint."""
    url = f"{app_url}/internal/poll"
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=body,
        headers={"X-Ingest-Secret": secret, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            log.info("Ingest accepted: HTTP %d", resp.status)
    except urllib.error.URLError as exc:
        log.error("Ingest POST failed: %s", exc)


def lambda_handler(event: dict, context: object) -> dict:
    event_type = event.get("type", "poll")
    label = event.get("label", "")
    app_url = os.environ["APP_RUNNER_URL"].rstrip("/")
    secret = _get_ingest_secret()

    players = _get_players(app_url, secret)
    if not players:
        log.warning("No players returned from App Runner — skipping poll")
        return {"statusCode": 200, "fetched": 0}

    snapshots: dict[str, dict] = {}
    for player in players:
        player_id = str(player["id"])
        account_name = player.get("account_name")
        if not account_name:
            log.debug("Skipping player %s — account name not yet set", player_id)
            continue

        stats = fetch_player(account_name, base_url=TOURNAMENT_URL)
        if stats:
            snapshots[player_id] = stats
        else:
            log.debug("No hiscores data for %s (%s)", account_name, player_id)

    _post_ingest(app_url, secret, {
        "type": event_type,
        "label": label,
        "snapshots": snapshots,
    })

    log.info("Polled %d/%d players (type=%s)", len(snapshots), len(players), event_type)
    return {"statusCode": 200, "fetched": len(snapshots)}
