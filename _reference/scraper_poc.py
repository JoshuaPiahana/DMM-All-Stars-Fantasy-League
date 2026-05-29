"""
REFERENCE ONLY — POC scraper for DMM All Stars 3.

The hiscores fetch/parse logic here is solid and should be ported (not copied)
into app/services/scraper.py in the new project. Key things to reuse:
  - fetch_hiscores(): the CSV parsing loop, activity index mapping, name building
  - build_account_name(): team prefix + display_name construction
  - The TIMEOUT, error handling, and 404 handling pattern

NOTE: This version imports from a flat sqlite `database` module — replace with
SQLAlchemy models. The ACTIVITY_NAMES list is also incomplete for the new
scoring system; it needs all boss kill counter names added.
"""

import requests
import logging
from datetime import datetime, timezone

TIMEOUT = 10  # seconds per request

log = logging.getLogger(__name__)

HISCORE_BASE_URL = "https://secure.runescape.com/m=hiscore_oldschool_tournament/index_lite.ws"

SKILLS = [
    "overall", "attack", "defence", "strength", "hitpoints",
    "ranged", "prayer", "magic", "cooking", "woodcutting",
    "fletching", "fishing", "firemaking", "crafting", "smithing",
    "mining", "herblore", "agility", "thieving", "slayer",
    "farming", "runecraft", "hunter", "construction",
]

# Indices 0-17 cover the non-boss activities before boss kill counters begin.
# Boss kill counters follow in the CSV — exact start index TBD from live endpoint.
# Needs extending with all boss names in correct hiscores order.
ACTIVITY_NAMES = [
    "league_points", "bounty_hunter_hunter", "bounty_hunter_rogue",
    "bounty_hunter_hunter_legacy", "bounty_hunter_rogue_legacy",
    "clue_scrolls_all", "clue_scrolls_beginner", "clue_scrolls_easy",
    "clue_scrolls_medium", "clue_scrolls_hard", "clue_scrolls_elite",
    "clue_scrolls_master", "lms_rank", "pvp_arena_rank",
    "soul_wars_zeal", "rifts_closed", "colosseum_glory",
    "collections_logged",
    # TODO: Add all boss kill counter names here in hiscores CSV order.
    # Boss names to add (verify exact API key spelling against live endpoint):
    # abyssal_sire, alchemical_hydra, artio, barrows_chests, bryophyta,
    # callisto, calvarion, cerberus, chambers_of_xeric,
    # chambers_of_xeric_challenge_mode, chaos_elemental, chaos_fanatic,
    # commander_zilyana, corporeal_beast, crazy_archaeologist,
    # dagannoth_prime, dagannoth_rex, dagannoth_supreme,
    # deranged_archaeologist, general_graardor, giant_mole,
    # grotesque_guardians, hespori, kalphite_queen, king_black_dragon,
    # kraken, kreearraa, kril_tsutsaroth, mimic, nex, nightmare,
    # obor, phantom_muspah, sarachnis, scorpia, scurrius, skotizo,
    # spindel, tempoross, the_corrupted_gauntlet, the_gauntlet,
    # theatre_of_blood, theatre_of_blood_hard_mode,
    # thermonuclear_smoke_devil, tombs_of_amascut,
    # tombs_of_amascut_expert_mode, tzkal_zuk, tztok_jad,
    # vardorvis, venenatis, vetion, vorkath, wintertodt,
    # zalcano, zulrah, guardians_of_the_rift
]


def build_account_name(player: dict, team_prefixes: dict) -> str | None:
    """
    Return the in-game DMM account name for a player.
    team_prefixes: {team_name: prefix_string} — sourced from DB (commissioner-configurable).
    """
    if player.get("account_name"):
        return player["account_name"]
    real_team = player.get("real_team")
    if not real_team:
        return None
    prefix = team_prefixes.get(real_team, "")
    return f"{prefix} {player['display_name']}" if prefix else None


def fetch_hiscores(account_name: str) -> dict | None:
    """
    Fetch a player's tournament hiscores.
    Returns dict of parsed stats, or None on 404/error.
    """
    try:
        resp = requests.get(
            HISCORE_BASE_URL,
            params={"player": account_name},
            timeout=TIMEOUT,
        )
        if resp.status_code == 404:
            log.debug("Player not found: %s", account_name)
            return None
        resp.raise_for_status()
    except requests.RequestException as e:
        log.warning("Hiscores request failed for %s: %s", account_name, e)
        return None

    lines = resp.text.strip().split("\n")
    data = {}

    for i, skill in enumerate(SKILLS):
        if i >= len(lines):
            break
        parts = lines[i].split(",")
        if len(parts) < 3:
            continue
        try:
            data[f"{skill}_xp"] = max(0, int(parts[2]))
            data[f"{skill}_level"] = max(0, int(parts[1]))
            if skill == "overall":
                data["overall_rank"] = int(parts[0])
        except ValueError:
            pass

    activity_start = len(SKILLS)
    for j, act in enumerate(ACTIVITY_NAMES):
        idx = activity_start + j
        if idx >= len(lines):
            break
        parts = lines[idx].split(",")
        if len(parts) < 2:
            continue
        try:
            data[act] = max(0, int(parts[1]))
        except ValueError:
            pass

    # PvP kills: bounty_hunter_hunter is the best available proxy
    data["pvp_kills"] = data.pop("bounty_hunter_hunter", 0)

    return data
