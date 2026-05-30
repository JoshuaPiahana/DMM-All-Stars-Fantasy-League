from flask import Blueprint, abort, jsonify, render_template

from app.extensions import db
from app.models import League, Manager

bp = Blueprint("public", __name__)


@bp.route("/health")
def health():
    return jsonify({"status": "ok"})


@bp.route("/")
def index():
    league = db.session.query(League).first()
    return render_template("index.html", league=league)


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
