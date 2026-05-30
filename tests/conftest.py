import pytest

from app import create_app
from app.extensions import db as _db
from app.seed import seed_if_empty


@pytest.fixture
def app():
    """Fresh in-memory SQLite DB per test — no cross-test bleed."""
    _app = create_app("testing")
    with _app.app_context():
        _db.create_all()
        yield _app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def seeded_app(app):
    """App with all 30 players and 6 teams seeded."""
    seed_if_empty()
    return app
