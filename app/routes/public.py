from __future__ import annotations

import json

from flask import Blueprint, abort, jsonify, render_template, request

from app.extensions import db
from app.models import HiscoreSnapshot, League, Manager, Player, RosterEntry
from app.services.scoring import (
    CATEGORY_LABELS,
    CATEGORY_ORDER,
    compute_category_scores,
    matchup_pairs,
    resolve_matchup,
)
from app.services.scoring_data import (
    compute_standings,
    current_event_day,
    manager_scores,
    player_delta,
)

bp = Blueprint("public", __name__)


@bp.route("/health")
def health():
    return jsonify({"status": "ok"})


@bp.route("/")
def index():
    league = db.session.query(League).first()
    today_day = current_event_day()
    standings: list[dict] = []
    today_matchups: list[dict] = []

    if league:
        managers = (
            db.session.query(Manager)
            .filter_by(league_id=league.id)
            .order_by(Manager.pick_position)
            .all()
        )
        if managers:
            standings = compute_standings(managers, through_day=today_day or 0)

        if today_day:
            pos_to_mgr = {m.pick_position: m for m in managers if m.pick_position}
            for pos_a, pos_b in matchup_pairs(today_day):
                mgr_a = pos_to_mgr.get(pos_a)
                mgr_b = pos_to_mgr.get(pos_b)
                if mgr_a and mgr_b:
                    _, scores_a = manager_scores(mgr_a.id)
                    _, scores_b = manager_scores(mgr_b.id)
                    result = resolve_matchup(scores_a, scores_b)
                    today_matchups.append({
                        "manager_a": mgr_a, "manager_b": mgr_b,
                        "scores_a": scores_a, "scores_b": scores_b,
                        "result": result, "day": today_day,
                    })

    return render_template(
        "index.html",
        league=league,
        standings=standings,
        today_matchups=today_matchups,
        today_day=today_day,
        category_labels=CATEGORY_LABELS,
        category_order=CATEGORY_ORDER,
    )


@bp.route("/league/<code>")
def league_page(code: str):
    league = db.session.query(League).filter_by(code=code).first()
    if not league:
        abort(404)
    managers = (
        db.session.query(Manager)
        .filter_by(league_id=league.id)
        .order_by(Manager.name)
        .all()
    )
    return render_template("league.html", league=league, managers=managers)


@bp.route("/matchup/<int:day>")
def matchup(day: int):
    try:
        pairs = matchup_pairs(day)
    except ValueError:
        abort(404)

    league = db.session.query(League).first()
    if not league:
        abort(404)

    managers = db.session.query(Manager).filter_by(league_id=league.id).all()
    pos_to_mgr = {m.pick_position: m for m in managers if m.pick_position}

    matchup_data: list[dict] = []
    for pos_a, pos_b in pairs:
        mgr_a = pos_to_mgr.get(pos_a)
        mgr_b = pos_to_mgr.get(pos_b)
        if mgr_a and mgr_b:
            _, scores_a = manager_scores(mgr_a.id)
            _, scores_b = manager_scores(mgr_b.id)
            result = resolve_matchup(scores_a, scores_b)
        else:
            scores_a = scores_b = {}
            result = {"category_results": {}, "wins_a": 0, "wins_b": 0, "matchup_winner": None}
        matchup_data.append({
            "manager_a": mgr_a, "manager_b": mgr_b,
            "scores_a": scores_a, "scores_b": scores_b,
            "result": result,
        })

    prev_day = day - 1 if day > 1 else None
    next_day = day + 1 if day < 9 else None
    return render_template(
        "matchup.html",
        day=day, matchups=matchup_data,
        prev_day=prev_day, next_day=next_day,
        category_labels=CATEGORY_LABELS,
        category_order=CATEGORY_ORDER,
    )


@bp.route("/roster/<token>")
def roster(token: str):
    manager = db.session.query(Manager).filter_by(token=token).first()
    if not manager:
        abort(404)

    entries = (
        db.session.query(RosterEntry)
        .filter_by(manager_id=manager.id)
        .order_by(RosterEntry.pick_number)
        .all()
    )

    players_data: list[dict] = []
    for entry in entries:
        delta = player_delta(entry.player_id)
        scores = compute_category_scores(delta)
        players_data.append({
            "player": entry.player,
            "pick_number": entry.pick_number,
            "scores": scores,
        })

    _, roster_scores = manager_scores(manager.id)
    return render_template(
        "roster.html",
        manager=manager,
        players=players_data,
        roster_scores=roster_scores,
        category_labels=CATEGORY_LABELS,
        category_order=CATEGORY_ORDER,
    )


@bp.route("/player/<int:player_id>")
def player_detail(player_id: int):
    player = db.session.get(Player, player_id)
    if not player:
        abort(404)

    snapshots = (
        db.session.query(HiscoreSnapshot)
        .filter_by(player_id=player_id)
        .order_by(HiscoreSnapshot.snapped_at)
        .all()
    )

    delta = player_delta(player_id)
    scores = compute_category_scores(delta)

    roster_entry = db.session.query(RosterEntry).filter_by(player_id=player_id).first()

    combat_fields = ["attack_xp", "defence_xp", "strength_xp", "hitpoints_xp",
                     "ranged_xp", "prayer_xp", "magic_xp"]
    chart_data = json.dumps({
        "timestamps": [s.snapped_at.isoformat() for s in snapshots],
        "combat_xp": [sum(getattr(s, f, 0) for f in combat_fields) for s in snapshots],
        "pvp_kills": [s.pvp_kills for s in snapshots],
    })

    return render_template(
        "player.html",
        player=player,
        delta=delta,
        scores=scores,
        roster_entry=roster_entry,
        chart_data=chart_data,
        snapshot_count=len(snapshots),
        category_labels=CATEGORY_LABELS,
        category_order=CATEGORY_ORDER,
    )


@bp.route("/leaderboard")
def leaderboard():
    sort_by = request.args.get("by", "combat_xp")
    if sort_by not in CATEGORY_ORDER:
        sort_by = "combat_xp"

    players = db.session.query(Player).all()
    players_data: list[dict] = []
    for player in players:
        delta = player_delta(player.id)
        scores = compute_category_scores(delta)
        entry = db.session.query(RosterEntry).filter_by(player_id=player.id).first()
        players_data.append({
            "player": player,
            "scores": scores,
            "manager": entry.manager if entry else None,
        })

    reverse = sort_by != "deaths"
    players_data.sort(key=lambda p: p["scores"].get(sort_by, 0), reverse=reverse)

    return render_template(
        "leaderboard.html",
        players=players_data,
        sort_by=sort_by,
        category_labels=CATEGORY_LABELS,
        category_order=CATEGORY_ORDER,
    )
