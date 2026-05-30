import os
from flask import Flask
from .config import config_by_name
from .extensions import db, migrate


def create_app(config_name: str | None = None) -> Flask:
    if config_name is None:
        config_name = os.environ.get("FLASK_CONFIG", "development")

    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    db.init_app(app)

    from . import models  # noqa: F401 — register all models with SQLAlchemy metadata

    migrate.init_app(app, db)

    from .routes.public import bp as public_bp
    app.register_blueprint(public_bp)

    @app.cli.command("seed")
    def seed_command() -> None:
        """Seed initial player and team data (idempotent)."""
        from .seed import seed_if_empty
        db.create_all()
        seed_if_empty()

    return app
