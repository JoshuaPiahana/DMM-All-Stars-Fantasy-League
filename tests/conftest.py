import pytest

from app import create_app
from app.extensions import db as _db


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
