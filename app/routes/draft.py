from __future__ import annotations

import json
import queue
import random
import threading
from collections.abc import Generator
from datetime import UTC, datetime

from flask import Blueprint, Response, jsonify, render_template, request, stream_with_context

from app.extensions import db
from app.models import DraftState, League, Manager, Player, RosterEntry
from app.services.draft_logic import is_draft_complete, validate_pick

bp = Blueprint("draft", __name__)

_TOTAL_PICKS = 30  # 6 managers × 5 rounds

_subscribers: list[queue.Queue] = []
_lock = threading.Lock()


def _subscribe() -> queue.Queue:
    q: queue.Queue = queue.Queue(maxsize=100)
    with _lock:
        _subscribers.append(q)
    return q


def _unsubscribe(q: queue.Queue) -> None:
    with _lock:
        try:
            _subscribers.remove(q)
        except ValueError:
            pass


def broadcast(event_type: str, data: dict) -> None:
    msg = f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
    with _lock:
        alive = []
        for q in _subscribers:
            try:
                q.put_nowait(msg)
                alive.append(q)
            except queue.Full:
                pass
        _subscribers[:] = alive


def _event_stream(q: queue.Queue) -> Generator[str, None, None]:
    try:
        while True:
            try:
                yield q.get(timeout=30)
            except queue.Empty:
                yield ": keepalive\n\n"
    finally:
        _unsubscribe(q)


@bp.route("/draft")
def draft_room():
    league = db.session.query(League).first()
    state = db.session.query(DraftState).first() if league else None
    players = db.session.query(Player).order_by(Player.display_name).all()
    entries = (
        db.session.query(RosterEntry).order_by(RosterEntry.pick_number).all()
        if state else []
    )
    drafted_ids = {e.player_id for e in entries}
    available = [p for p in players if p.id not in drafted_ids]
    return render_template(
        "draft.html",
        league=league,
        state=state,
        available=available,
        entries=entries,
        total_picks=_TOTAL_PICKS,
    )


@bp.route("/draft/stream")
def draft_stream():
    q = _subscribe()
    return Response(
        stream_with_context(_event_stream(q)),
        content_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@bp.route("/draft/start", methods=["POST"])
def draft_start():
    comm_token = request.headers.get("X-Commissioner-Token", "")
    if not comm_token:
        return jsonify({"error": "Missing commissioner token"}), 401

    league = db.session.query(League).filter_by(commissioner_token=comm_token).first()
    if not league:
        return jsonify({"error": "Invalid commissioner token"}), 401

    state = db.session.query(DraftState).filter_by(league_id=league.id).first()
    if not state:
        return jsonify({"error": "No draft state"}), 404
    if state.started_at is not None:
        return jsonify({"error": "Draft already started"}), 409

    managers = db.session.query(Manager).filter_by(league_id=league.id).all()
    positions = list(range(1, len(managers) + 1))
    random.shuffle(positions)
    for mgr, pos in zip(managers, positions):
        mgr.pick_position = pos

    state.started_at = datetime.now(UTC)
    db.session.commit()

    broadcast("start", {"current_pick": 0, "total_picks": _TOTAL_PICKS})
    return jsonify({"status": "started", "current_pick": 0}), 200


@bp.route("/draft/pick", methods=["POST"])
def draft_pick():
    mgr_token = request.headers.get("X-Manager-Token", "")
    if not mgr_token:
        return jsonify({"error": "Missing manager token"}), 401

    manager = db.session.query(Manager).filter_by(token=mgr_token).first()
    if not manager:
        return jsonify({"error": "Invalid manager token"}), 401

    league = db.session.get(League, manager.league_id)
    state = db.session.query(DraftState).filter_by(league_id=league.id).first()

    if manager.pick_position is None:
        return jsonify({"error": "Draft not yet started"}), 409

    err = validate_pick(
        current_pick=state.current_pick,
        total_picks=_TOTAL_PICKS,
        manager_position=manager.pick_position,
        started=state.started_at is not None,
        completed=state.completed_at is not None,
    )
    if err:
        return jsonify({"error": err}), 409

    body = request.get_json(silent=True) or {}
    player_id = body.get("player_id")
    if not player_id:
        return jsonify({"error": "player_id required"}), 400

    player = db.session.get(Player, player_id)
    if not player:
        return jsonify({"error": "Player not found"}), 404

    if db.session.query(RosterEntry).filter_by(player_id=player_id).first():
        return jsonify({"error": "Player already drafted"}), 409

    pick_number = state.current_pick + 1
    db.session.add(RosterEntry(
        manager_id=manager.id,
        player_id=player_id,
        pick_number=pick_number,
        drafted_at=datetime.now(UTC),
    ))

    state.current_pick += 1
    if is_draft_complete(state.current_pick, _TOTAL_PICKS):
        state.completed_at = datetime.now(UTC)

    db.session.commit()

    event_data = {
        "pick_number": pick_number,
        "manager_id": manager.id,
        "manager_name": manager.name,
        "player_id": player_id,
        "player_name": player.display_name,
        "current_pick": state.current_pick,
    }
    broadcast("pick", event_data)
    if state.completed_at:
        broadcast("complete", {"total_picks": _TOTAL_PICKS})

    return jsonify(event_data), 200
