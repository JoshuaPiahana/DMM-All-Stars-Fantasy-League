"""Tests for SQLAlchemy models and seed data. Written before model implementation (TDD)."""

from datetime import datetime, timezone

import pytest

from app.extensions import db
from app.models import Death, DraftState, HiscoreSnapshot, League, Manager, Player, RealTeam, RosterEntry
from app.seed import seed_if_empty


# ── RealTeam ──────────────────────────────────────────────────────────────────

def test_real_team_fields(app):
    with app.app_context():
        team = RealTeam(name="Odablock Warriors", color="#dc2626", prefix="")
        db.session.add(team)
        db.session.flush()
        assert team.id is not None
        assert team.name == "Odablock Warriors"
        assert team.color == "#dc2626"
        assert team.prefix == ""


# ── Player ────────────────────────────────────────────────────────────────────

def test_player_fields(app):
    with app.app_context():
        player = Player(display_name="EVScape", is_captain=False)
        db.session.add(player)
        db.session.flush()
        assert player.id is not None
        assert player.real_team_id is None
        assert player.account_name_override is None


def test_player_captain_flag(app):
    with app.app_context():
        captain = Player(display_name="Odablock", is_captain=True)
        db.session.add(captain)
        db.session.flush()
        assert captain.is_captain is True


def test_player_account_name_with_prefix(app):
    with app.app_context():
        team = RealTeam(name="Test Team", color="#ffffff", prefix="TS")
        db.session.add(team)
        db.session.flush()
        player = Player(display_name="Odablock", is_captain=True, real_team_id=team.id)
        db.session.add(player)
        db.session.flush()
        assert player.account_name == "TS Odablock"


def test_player_account_name_no_prefix(app):
    with app.app_context():
        team = RealTeam(name="Test Team 2", color="#000000", prefix="")
        db.session.add(team)
        db.session.flush()
        player = Player(display_name="Framed", is_captain=True, real_team_id=team.id)
        db.session.add(player)
        db.session.flush()
        assert player.account_name is None


def test_player_account_name_override(app):
    with app.app_context():
        team = RealTeam(name="Test Team 3", color="#111111", prefix="TS")
        db.session.add(team)
        db.session.flush()
        player = Player(
            display_name="Westham",
            is_captain=True,
            real_team_id=team.id,
            account_name_override="WH Westham Custom",
        )
        db.session.add(player)
        db.session.flush()
        assert player.account_name == "WH Westham Custom"


def test_player_no_team_no_account_name(app):
    with app.app_context():
        player = Player(display_name="Synq", is_captain=False)
        assert player.account_name is None


# ── League ────────────────────────────────────────────────────────────────────

def test_league_fields(app):
    with app.app_context():
        league = League(
            code="DMMX7K2F",
            commissioner_token="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            created_at=datetime(2026, 5, 31, tzinfo=timezone.utc),
        )
        db.session.add(league)
        db.session.flush()
        assert league.id is not None
        assert league.code == "DMMX7K2F"


# ── Manager ───────────────────────────────────────────────────────────────────

def test_manager_links_to_league(app):
    with app.app_context():
        league = League(
            code="TESTLG01",
            commissioner_token="ffffffff-0000-1111-2222-333333333333",
            created_at=datetime(2026, 5, 31, tzinfo=timezone.utc),
        )
        db.session.add(league)
        db.session.flush()
        mgr = Manager(
            league_id=league.id,
            name="Alice",
            token="11111111-2222-3333-4444-555555555555",
        )
        db.session.add(mgr)
        db.session.flush()
        assert mgr.league_id == league.id
        assert mgr.pick_position is None


# ── RosterEntry ───────────────────────────────────────────────────────────────

def test_roster_entry_links_manager_and_player(app):
    with app.app_context():
        league = League(
            code="ROST0001",
            commissioner_token="aaaa0000-bbbb-cccc-dddd-eeeeeeeeeeee",
            created_at=datetime(2026, 5, 31, tzinfo=timezone.utc),
        )
        db.session.add(league)
        mgr = Manager(league=league, name="Bob", token="bbbb0000-1111-2222-3333-444444444444")
        db.session.add(mgr)
        player = Player(display_name="B0aty", is_captain=False)
        db.session.add(player)
        db.session.flush()

        entry = RosterEntry(
            manager=mgr,
            player=player,
            pick_number=1,
            drafted_at=datetime(2026, 5, 31, 20, 0, tzinfo=timezone.utc),
        )
        db.session.add(entry)
        db.session.flush()
        assert entry.manager_id == mgr.id
        assert entry.player_id == player.id


# ── DraftState ────────────────────────────────────────────────────────────────

def test_draft_state_initial_pick_zero(app):
    with app.app_context():
        league = League(
            code="DRFT0001",
            commissioner_token="cccc0000-dddd-eeee-ffff-000000000000",
            created_at=datetime(2026, 5, 31, tzinfo=timezone.utc),
        )
        db.session.add(league)
        db.session.flush()
        state = DraftState(league_id=league.id)
        db.session.add(state)
        db.session.flush()
        assert state.current_pick == 0
        assert state.started_at is None
        assert state.completed_at is None


# ── HiscoreSnapshot ───────────────────────────────────────────────────────────

def test_hiscore_snapshot_defaults_to_zero(app):
    with app.app_context():
        player = Player(display_name="Coxie", is_captain=False)
        db.session.add(player)
        db.session.flush()
        snap = HiscoreSnapshot(
            player_id=player.id,
            snapshot_type="poll",
            snapped_at=datetime(2026, 6, 6, 12, 0, tzinfo=timezone.utc),
        )
        db.session.add(snap)
        db.session.flush()
        assert snap.attack_xp == 0
        assert snap.pvp_kills == 0
        assert snap.zulrah == 0
        assert snap.chambers_of_xeric == 0
        assert snap.deaths_cumulative == 0


def test_hiscore_snapshot_stores_values(app):
    with app.app_context():
        player = Player(display_name="Torvesta", is_captain=False)
        db.session.add(player)
        db.session.flush()
        snap = HiscoreSnapshot(
            player_id=player.id,
            snapshot_type="baseline",
            snapped_at=datetime(2026, 6, 6, 11, 0, tzinfo=timezone.utc),
            attack_xp=500_000,
            strength_xp=800_000,
            pvp_kills=12,
            zulrah=5,
            chambers_of_xeric=3,
        )
        db.session.add(snap)
        db.session.flush()
        assert snap.attack_xp == 500_000
        assert snap.pvp_kills == 12
        assert snap.zulrah == 5


# ── Death ─────────────────────────────────────────────────────────────────────

def test_death_entry(app):
    with app.app_context():
        player = Player(display_name="Skiddler", is_captain=False)
        db.session.add(player)
        db.session.flush()
        death = Death(
            player_id=player.id,
            cumulative_count=3,
            recorded_at=datetime(2026, 6, 7, 14, 0, tzinfo=timezone.utc),
        )
        db.session.add(death)
        db.session.flush()
        assert death.cumulative_count == 3


# ── Seed ──────────────────────────────────────────────────────────────────────

def test_seed_creates_30_players(app):
    with app.app_context():
        seed_if_empty()
        total = db.session.query(Player).count()
        assert total == 30


def test_seed_creates_6_real_teams(app):
    with app.app_context():
        seed_if_empty()
        total = db.session.query(RealTeam).count()
        assert total == 6


def test_seed_creates_6_captains(app):
    with app.app_context():
        seed_if_empty()
        captains = db.session.query(Player).filter_by(is_captain=True).count()
        assert captains == 6


def test_seed_idempotent(app):
    with app.app_context():
        seed_if_empty()
        seed_if_empty()
        assert db.session.query(Player).count() == 30
        assert db.session.query(RealTeam).count() == 6


def test_seed_captains_linked_to_teams(app):
    with app.app_context():
        seed_if_empty()
        captains = db.session.query(Player).filter_by(is_captain=True).all()
        for captain in captains:
            assert captain.real_team_id is not None


def test_seed_draftable_players_have_no_team(app):
    with app.app_context():
        seed_if_empty()
        draftable = db.session.query(Player).filter_by(is_captain=False).all()
        assert len(draftable) == 24
        for player in draftable:
            assert player.real_team_id is None
