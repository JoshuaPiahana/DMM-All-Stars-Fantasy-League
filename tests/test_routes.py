"""Integration tests for all routes — uses Flask test client + in-memory SQLite."""
import pytest

from app.extensions import db
from app.models import DraftState, HiscoreSnapshot, League, Manager, Player

# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def league_data(seeded_app):
    """POST /create and return the response payload."""
    client = seeded_app.test_client()
    resp = client.post(
        "/create",
        json={"managers": ["Alice", "Bob", "Charlie", "Dave", "Eve", "Frank"]},
    )
    assert resp.status_code == 201
    return resp.get_json()


def _start_draft(client, comm_token: str) -> None:
    resp = client.post("/draft/start", headers={"X-Commissioner-Token": comm_token})
    assert resp.status_code == 200, resp.get_json()


# ── /create ───────────────────────────────────────────────────────────────────

def test_create_returns_201(client):
    resp = client.post(
        "/create",
        json={"managers": ["Alice", "Bob", "Charlie", "Dave", "Eve", "Frank"]},
    )
    assert resp.status_code == 201


def test_create_returns_league_code_and_tokens(client):
    resp = client.post(
        "/create",
        json={"managers": ["Alice", "Bob", "Charlie", "Dave", "Eve", "Frank"]},
    )
    data = resp.get_json()
    assert len(data["league_code"]) == 8
    assert len(data["commissioner_token"]) == 36
    assert len(data["managers"]) == 6
    for m in data["managers"]:
        assert "id" in m
        assert "name" in m
        assert len(m["token"]) == 36


def test_create_requires_exactly_6_managers(client):
    resp = client.post("/create", json={"managers": ["Alice", "Bob"]})
    assert resp.status_code == 400


def test_create_persists_to_db(app):
    app.test_client().post(
        "/create",
        json={"managers": ["Alice", "Bob", "Charlie", "Dave", "Eve", "Frank"]},
    )
    assert db.session.query(League).count() == 1
    assert db.session.query(Manager).count() == 6
    assert db.session.query(DraftState).count() == 1


def test_create_get_returns_200(client):
    resp = client.get("/create")
    assert resp.status_code == 200


# ── /league/<code> ────────────────────────────────────────────────────────────

def test_get_league_page_200(seeded_app, league_data):
    resp = seeded_app.test_client().get(f"/league/{league_data['league_code']}")
    assert resp.status_code == 200


def test_get_league_page_404_unknown(seeded_app):
    resp = seeded_app.test_client().get("/league/BADCODE1")
    assert resp.status_code == 404


def test_get_manager_token(seeded_app, league_data):
    code = league_data["league_code"]
    manager = league_data["managers"][0]
    resp = seeded_app.test_client().get(f"/league/{code}/manager/{manager['id']}/token")
    assert resp.status_code == 200
    assert resp.get_json()["token"] == manager["token"]


def test_get_manager_token_wrong_league(seeded_app, league_data):
    manager_id = league_data["managers"][0]["id"]
    resp = seeded_app.test_client().get(f"/league/BADCODE1/manager/{manager_id}/token")
    assert resp.status_code == 404


def test_get_manager_token_wrong_manager(seeded_app, league_data):
    code = league_data["league_code"]
    resp = seeded_app.test_client().get(f"/league/{code}/manager/99999/token")
    assert resp.status_code == 404


# ── /draft/start ──────────────────────────────────────────────────────────────

def test_draft_start_requires_token(seeded_app, league_data):
    resp = seeded_app.test_client().post("/draft/start")
    assert resp.status_code == 401


def test_draft_start_wrong_token(seeded_app, league_data):
    resp = seeded_app.test_client().post(
        "/draft/start", headers={"X-Commissioner-Token": "wrong"},
    )
    assert resp.status_code == 401


def test_draft_start_assigns_positions(seeded_app, league_data):
    _start_draft(seeded_app.test_client(), league_data["commissioner_token"])
    db.session.expire_all()
    managers = db.session.query(Manager).all()
    positions = sorted(m.pick_position for m in managers)
    assert positions == [1, 2, 3, 4, 5, 6]


def test_draft_start_sets_started_at(seeded_app, league_data):
    _start_draft(seeded_app.test_client(), league_data["commissioner_token"])
    db.session.expire_all()
    state = db.session.query(DraftState).first()
    assert state.started_at is not None


def test_draft_start_idempotent_fails_second_time(seeded_app, league_data):
    client = seeded_app.test_client()
    _start_draft(client, league_data["commissioner_token"])
    resp = client.post(
        "/draft/start", headers={"X-Commissioner-Token": league_data["commissioner_token"]},
    )
    assert resp.status_code == 409


# ── /draft/pick ───────────────────────────────────────────────────────────────

def test_draft_pick_requires_token(seeded_app, league_data):
    _start_draft(seeded_app.test_client(), league_data["commissioner_token"])
    resp = seeded_app.test_client().post("/draft/pick", json={"player_id": 1})
    assert resp.status_code == 401


def test_draft_pick_invalid_token(seeded_app, league_data):
    _start_draft(seeded_app.test_client(), league_data["commissioner_token"])
    resp = seeded_app.test_client().post(
        "/draft/pick",
        json={"player_id": 1},
        headers={"X-Manager-Token": "bad-token"},
    )
    assert resp.status_code == 401


def test_draft_pick_not_your_turn(seeded_app, league_data):
    """Manager at position 2 cannot pick when it's position 1's turn."""
    client = seeded_app.test_client()
    _start_draft(client, league_data["commissioner_token"])
    db.session.expire_all()
    mgr = db.session.query(Manager).filter_by(pick_position=2).first()
    player_id = db.session.query(Player).first().id
    resp = client.post(
        "/draft/pick",
        json={"player_id": player_id},
        headers={"X-Manager-Token": mgr.token},
    )
    assert resp.status_code == 409


def test_draft_pick_success(seeded_app, league_data):
    client = seeded_app.test_client()
    _start_draft(client, league_data["commissioner_token"])
    db.session.expire_all()
    mgr = db.session.query(Manager).filter_by(pick_position=1).first()
    player_id = db.session.query(Player).first().id
    resp = client.post(
        "/draft/pick",
        json={"player_id": player_id},
        headers={"X-Manager-Token": mgr.token},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["player_id"] == player_id
    assert data["pick_number"] == 1


def test_draft_pick_advances_current_pick(seeded_app, league_data):
    client = seeded_app.test_client()
    _start_draft(client, league_data["commissioner_token"])
    db.session.expire_all()
    mgr = db.session.query(Manager).filter_by(pick_position=1).first()
    player_id = db.session.query(Player).first().id
    client.post(
        "/draft/pick",
        json={"player_id": player_id},
        headers={"X-Manager-Token": mgr.token},
    )
    db.session.expire_all()
    assert db.session.query(DraftState).first().current_pick == 1


def test_draft_pick_player_already_taken(seeded_app, league_data):
    client = seeded_app.test_client()
    _start_draft(client, league_data["commissioner_token"])
    db.session.expire_all()
    mgr1 = db.session.query(Manager).filter_by(pick_position=1).first()
    mgr2 = db.session.query(Manager).filter_by(pick_position=2).first()
    player_id = db.session.query(Player).first().id
    # position 1 picks the player
    client.post("/draft/pick", json={"player_id": player_id},
                headers={"X-Manager-Token": mgr1.token})
    # position 2 tries to pick the same player
    resp = client.post(
        "/draft/pick",
        json={"player_id": player_id},
        headers={"X-Manager-Token": mgr2.token},
    )
    assert resp.status_code == 409


# ── /internal/players ────────────────────────────────────────────────────────

def test_internal_players_requires_secret(seeded_app):
    resp = seeded_app.test_client().get("/internal/players")
    assert resp.status_code == 401


def test_internal_players_wrong_secret(seeded_app):
    resp = seeded_app.test_client().get(
        "/internal/players", headers={"X-Ingest-Secret": "wrong"},
    )
    assert resp.status_code == 401


def test_internal_players_returns_all_players(seeded_app):
    resp = seeded_app.test_client().get(
        "/internal/players",
        headers={"X-Ingest-Secret": seeded_app.config["INGEST_SECRET"]},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data) == 30
    for item in data:
        assert "id" in item
        assert "account_name" in item


# ── /internal/poll ────────────────────────────────────────────────────────────

def test_internal_poll_requires_secret(seeded_app):
    resp = seeded_app.test_client().post(
        "/internal/poll",
        json={"type": "poll", "label": "", "snapshots": {}},
    )
    assert resp.status_code == 401


def test_internal_poll_stores_snapshots(seeded_app):
    player_id = db.session.query(Player).first().id
    resp = seeded_app.test_client().post(
        "/internal/poll",
        json={
            "type": "poll",
            "label": "",
            "snapshots": {str(player_id): {"attack_xp": 500_000, "pvp_kills": 5}},
        },
        headers={"X-Ingest-Secret": seeded_app.config["INGEST_SECRET"]},
    )
    assert resp.status_code == 200
    assert resp.get_json()["stored"] == 1


def test_internal_poll_ignores_unknown_player(seeded_app):
    resp = seeded_app.test_client().post(
        "/internal/poll",
        json={"type": "poll", "label": "", "snapshots": {"99999": {"attack_xp": 100}}},
        headers={"X-Ingest-Secret": seeded_app.config["INGEST_SECRET"]},
    )
    assert resp.status_code == 200
    assert resp.get_json()["stored"] == 0


def test_internal_poll_baseline_type_stored(seeded_app):
    player_id = db.session.query(Player).first().id
    seeded_app.test_client().post(
        "/internal/poll",
        json={
            "type": "baseline",
            "label": "2026-06-06T11:00:00Z",
            "snapshots": {str(player_id): {"zulrah": 10, "vorkath": 5}},
        },
        headers={"X-Ingest-Secret": seeded_app.config["INGEST_SECRET"]},
    )
    db.session.expire_all()
    snap = db.session.query(HiscoreSnapshot).filter_by(
        player_id=player_id, snapshot_type="baseline",
    ).first()
    assert snap is not None
    assert snap.zulrah == 10
    assert snap.vorkath == 5


# ── /draft page ───────────────────────────────────────────────────────────────

def test_draft_page_returns_200(seeded_app, league_data):
    resp = seeded_app.test_client().get("/draft")
    assert resp.status_code == 200
