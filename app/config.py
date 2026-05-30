import os


def _normalise_db_url(url: str) -> str:
    # SQLAlchemy 2.x requires postgresql://, not postgres://
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-change-me")
    SQLALCHEMY_DATABASE_URI = _normalise_db_url(
        os.environ.get("DATABASE_URL", "postgresql://localhost/dmm_fantasy")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    INGEST_SECRET = os.environ.get("INGEST_SECRET", "")


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    INGEST_SECRET = "test-ingest-secret"


class ProductionConfig(Config):
    pass  # all secrets injected via environment variables


config_by_name: dict[str, type[Config]] = {
    "development": Config,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
