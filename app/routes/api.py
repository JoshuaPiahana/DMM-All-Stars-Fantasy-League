from datetime import UTC, datetime

from flask import Blueprint, current_app, jsonify, request

from app.extensions import db
from app.models import HiscoreSnapshot, League, Manager, Player

bp = Blueprint("api", __name__)

_SNAPSHOT_STAT_KEYS = frozenset({
    "overall_xp", "attack_xp", "defence_xp", "strength_xp",
    "hitpoints_xp", "ranged_xp", "prayer_xp", "magic_xp",
    "cooking_xp", "woodcutting_xp", "fletching_xp", "fishing_xp",
    "firemaking_xp", "crafting_xp", "smithing_xp", "mining_xp",
    "herblore_xp", "agility_xp", "thieving_xp", "slayer_xp",
    "farming_xp", "runecraft_xp", "hunter_xp", "construction_xp",
    "pvp_kills",
    "barrows_chests", "wintertodt", "tempoross",
    "guardians_of_the_rift", "giant_mole", "king_black_dragon",
    "chaos_fanatic", "chaos_elemental", "scorpia",
    "crazy_archaeologist", "deranged_archaeologist",
    "kalphite_queen", "kraken", "thermonuclear_smoke_devil",
    "sarachnis", "skotizo", "dagannoth_prime", "dagannoth_rex",
    "dagannoth_supreme", "zalcano",
    "abyssal_sire", "cerberus", "corporeal_beast",
    "general_graardor", "commander_zilyana", "kreearra",
    "kril_tsutsaroth", "grotesque_guardians",
    "zulrah", "vorkath", "alchemical_hydra", "phantom_muspah", "nex",
    "chambers_of_xeric", "theatre_of_blood", "tombs_of_amascut",
})


def _ingest_auth() -> bool:
    secret = current_app.config.get("INGEST_SECRET", "")
    return bool(secret) and request.headers.get("X-Ingest-Secret") == secret


@bp.route("/internal/players")
def internal_players():
    if not _ingest_auth():
        return jsonify({"error": "Unauthorized"}), 401
    players = db.session.query(Player).all()
    return jsonify([{"id": p.id, "account_name": p.account_name} for p in players])


@bp.route("/internal/poll", methods=["POST"])
def internal_poll():
    if not _ingest_auth():
        return jsonify({"error": "Unauthorized"}), 401

    payload = request.get_json(silent=True) or {}
    snapshot_type = payload.get("type", "poll")
    snapshots: dict = payload.get("snapshots", {})

    stored = 0
    now = datetime.now(UTC)
    for player_id_str, stats in snapshots.items():
        try:
            player_id = int(player_id_str)
        except ValueError:
            continue
        if not db.session.get(Player, player_id):
            continue
        kwargs = {k: v for k, v in stats.items() if k in _SNAPSHOT_STAT_KEYS}
        db.session.add(HiscoreSnapshot(
            player_id=player_id,
            snapshot_type=snapshot_type,
            snapped_at=now,
            **kwargs,
        ))
        stored += 1

    db.session.commit()
    return jsonify({"stored": stored}), 200


@bp.route("/league/<code>/manager/<int:manager_id>/token")
def manager_token(code: str, manager_id: int):
    league = db.session.query(League).filter_by(code=code).first()
    if not league:
        return jsonify({"error": "League not found"}), 404
    manager = db.session.query(Manager).filter_by(
        id=manager_id, league_id=league.id,
    ).first()
    if not manager:
        return jsonify({"error": "Manager not found"}), 404
    return jsonify({"token": manager.token})
