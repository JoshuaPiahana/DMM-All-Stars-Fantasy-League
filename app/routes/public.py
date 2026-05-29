from flask import Blueprint, render_template, jsonify

bp = Blueprint("public", __name__)


@bp.route("/health")
def health():
    return jsonify({"status": "ok"})


@bp.route("/")
def index():
    return render_template("index.html")
