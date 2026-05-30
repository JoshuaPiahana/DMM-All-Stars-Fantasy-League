from datetime import UTC, datetime

from flask import Blueprint, jsonify, render_template, request

from app.extensions import db
from app.models import Death, DraftState, HiscoreSnapshot, League, Manager, Player, RealTeam
from app.services.draft_logic import generate_league_code, generate_token
from app.services.scraper import TOURNAMENT_URL, fetch_player

bp = Blueprint("commissioner", __name__)

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


def _auth() -> League | None:
    token = request.headers.get("X-Commissioner-Token", "")
    if not token:
        return None
    return db.session.query(League).filter_by(commissioner_token=token).first()


@bp.route("/create", methods=["GET"])
def create_get():
    return render_template("create.html")


@bp.route("/create", methods=["POST"])
def create_post():
    data = request.get_json(silent=True) or {}
    names = [n.strip() for n in data.get("managers", [])]
    if len(names) != 6:
        return jsonify({"error": "Exactly 6 manager names required"}), 400
    if len(set(names)) != 6:
        return jsonify({"error": "Manager names must be unique"}), 400

    code = generate_league_code()
    while db.session.query(League).filter_by(code=code).first():
        code = generate_league_code()

    league = League(
        code=code,
        commissioner_token=generate_token(),
        created_at=datetime.now(UTC),
    )
    db.session.add(league)
    db.session.flush()

    db.session.add(DraftState(league_id=league.id, current_pick=0))

    for name in names:
        db.session.add(Manager(league_id=league.id, name=name, token=generate_token()))

    db.session.commit()

    mgr_rows = db.session.query(Manager).filter_by(league_id=league.id).all()
    return jsonify({
        "league_code": league.code,
        "commissioner_token": league.commissioner_token,
        "managers": [{"id": m.id, "name": m.name, "token": m.token} for m in mgr_rows],
    }), 201


@bp.route("/commissioner")
def commissioner_panel():
    league = db.session.query(League).first()
    players = db.session.query(Player).order_by(Player.display_name).all()
    teams = db.session.query(RealTeam).order_by(RealTeam.name).all()
    managers = (
        db.session.query(Manager)
        .filter_by(league_id=league.id)
        .order_by(Manager.name)
        .all()
        if league else []
    )
    # Latest death count per player
    death_counts: dict[int, int] = {}
    for player in players:
        latest = (
            db.session.query(Death)
            .filter_by(player_id=player.id)
            .order_by(Death.recorded_at.desc())
            .first()
        )
        if latest:
            death_counts[player.id] = latest.cumulative_count
    return render_template(
        "commissioner.html",
        league=league,
        players=players,
        teams=teams,
        managers=managers,
        death_counts=death_counts,
    )


@bp.route("/commissioner/deaths", methods=["POST"])
def update_deaths():
    league = _auth()
    if not league:
        return jsonify({"error": "Unauthorized"}), 401

    body = request.get_json(silent=True) or {}
    player_id = body.get("player_id")
    count = body.get("count")
    if player_id is None or count is None:
        return jsonify({"error": "player_id and count required"}), 400

    player = db.session.get(Player, player_id)
    if not player:
        return jsonify({"error": "Player not found"}), 404

    db.session.add(Death(
        player_id=player_id,
        cumulative_count=int(count),
        recorded_at=datetime.now(UTC),
    ))
    db.session.commit()
    return jsonify({"player_id": player_id, "count": count}), 200


@bp.route("/commissioner/prefix", methods=["POST"])
def update_prefix():
    league = _auth()
    if not league:
        return jsonify({"error": "Unauthorized"}), 401

    body = request.get_json(silent=True) or {}
    team_id = body.get("team_id")
    prefix = body.get("prefix", "")
    if team_id is None:
        return jsonify({"error": "team_id required"}), 400

    team = db.session.get(RealTeam, team_id)
    if not team:
        return jsonify({"error": "Team not found"}), 404

    team.prefix = prefix.strip()
    db.session.commit()
    return jsonify({"team_id": team_id, "prefix": team.prefix}), 200


@bp.route("/commissioner/token/<int:manager_id>", methods=["POST"])
def reset_manager_token(manager_id: int):
    league = _auth()
    if not league:
        return jsonify({"error": "Unauthorized"}), 401

    manager = db.session.query(Manager).filter_by(
        id=manager_id, league_id=league.id,
    ).first()
    if not manager:
        return jsonify({"error": "Manager not found"}), 404

    manager.token = generate_token()
    db.session.commit()
    return jsonify({"manager_id": manager_id, "token": manager.token}), 200


@bp.route("/commissioner/refresh", methods=["POST"])
def manual_refresh():
    league = _auth()
    if not league:
        return jsonify({"error": "Unauthorized"}), 401

    players = db.session.query(Player).all()
    now = datetime.now(UTC)
    fetched = 0
    for player in players:
        account_name = player.account_name
        if not account_name:
            continue
        stats = fetch_player(account_name, base_url=TOURNAMENT_URL)
        if stats:
            kwargs = {k: v for k, v in stats.items() if k in _SNAPSHOT_STAT_KEYS}
            db.session.add(HiscoreSnapshot(
                player_id=player.id,
                snapshot_type="poll",
                snapped_at=now,
                **kwargs,
            ))
            fetched += 1

    db.session.commit()
    return jsonify({"fetched": fetched, "total": len(players)}), 200
