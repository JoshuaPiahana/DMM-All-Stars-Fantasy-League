from datetime import UTC, datetime

from flask import Blueprint, jsonify, render_template, request

from app.extensions import db
from app.models import DraftState, League, Manager
from app.services.draft_logic import generate_league_code, generate_token

bp = Blueprint("commissioner", __name__)


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
    return render_template("commissioner.html")
