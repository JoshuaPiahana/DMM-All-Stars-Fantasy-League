"""Tests for scoring_data — DB-backed helpers (needs app fixture)."""
from datetime import UTC, datetime

from app.extensions import db
from app.models import Death, DraftState, HiscoreSnapshot, League, Manager, Player, RosterEntry
from app.services.scoring_data import compute_standings, manager_scores, player_delta

# ── player_delta ──────────────────────────────────────────────────────────────

def test_player_delta_no_snapshots_all_zeros(seeded_app):
    player_id = db.session.query(Player).first().id
    assert all(v == 0 for v in player_delta(player_id).values())


def test_player_delta_poll_only_no_baseline(seeded_app):
    player = db.session.query(Player).first()
    db.session.add(HiscoreSnapshot(
        player_id=player.id,
        snapshot_type="poll",
        snapped_at=datetime(2026, 6, 6, 12, 0, tzinfo=UTC),
        attack_xp=500_000,
        zulrah=10,
    ))
    db.session.commit()
    delta = player_delta(player.id)
    assert delta["attack_xp"] == 500_000
    assert delta["zulrah"] == 10


def test_player_delta_subtracts_baseline(seeded_app):
    player = db.session.query(Player).first()
    db.session.add(HiscoreSnapshot(
        player_id=player.id,
        snapshot_type="baseline",
        snapped_at=datetime(2026, 6, 6, 11, 0, tzinfo=UTC),
        attack_xp=100_000,
        zulrah=2,
    ))
    db.session.add(HiscoreSnapshot(
        player_id=player.id,
        snapshot_type="poll",
        snapped_at=datetime(2026, 6, 6, 13, 0, tzinfo=UTC),
        attack_xp=250_000,
        zulrah=5,
    ))
    db.session.commit()
    delta = player_delta(player.id)
    assert delta["attack_xp"] == 150_000
    assert delta["zulrah"] == 3


def test_player_delta_uses_latest_poll(seeded_app):
    player = db.session.query(Player).first()
    db.session.add(HiscoreSnapshot(
        player_id=player.id, snapshot_type="poll",
        snapped_at=datetime(2026, 6, 6, 12, 0, tzinfo=UTC), attack_xp=100_000,
    ))
    db.session.add(HiscoreSnapshot(
        player_id=player.id, snapshot_type="poll",
        snapped_at=datetime(2026, 6, 6, 13, 0, tzinfo=UTC), attack_xp=200_000,
    ))
    db.session.commit()
    assert player_delta(player.id)["attack_xp"] == 200_000


def test_player_delta_overrides_deaths_with_manual_entry(seeded_app):
    player = db.session.query(Player).first()
    db.session.add(HiscoreSnapshot(
        player_id=player.id, snapshot_type="poll",
        snapped_at=datetime(2026, 6, 6, 12, 0, tzinfo=UTC),
    ))
    db.session.add(Death(
        player_id=player.id, cumulative_count=7,
        recorded_at=datetime(2026, 6, 6, 14, 0, tzinfo=UTC),
    ))
    db.session.commit()
    assert player_delta(player.id)["deaths_cumulative"] == 7


def test_player_delta_clamps_negative_to_zero(seeded_app):
    player = db.session.query(Player).first()
    db.session.add(HiscoreSnapshot(
        player_id=player.id, snapshot_type="baseline",
        snapped_at=datetime(2026, 6, 6, 11, 0, tzinfo=UTC), attack_xp=500_000,
    ))
    db.session.add(HiscoreSnapshot(
        player_id=player.id, snapshot_type="poll",
        snapped_at=datetime(2026, 6, 6, 12, 0, tzinfo=UTC), attack_xp=400_000,
    ))
    db.session.commit()
    assert player_delta(player.id)["attack_xp"] == 0


# ── manager_scores ────────────────────────────────────────────────────────────

def _make_league_and_manager(code: str, name: str, token: str) -> Manager:
    league = League(
        code=code,
        commissioner_token=token[:36],
        created_at=datetime(2026, 5, 31, tzinfo=UTC),
    )
    db.session.add(league)
    db.session.flush()
    mgr = Manager(league_id=league.id, name=name, token=token)
    db.session.add(mgr)
    db.session.commit()
    return mgr


def test_manager_scores_empty_roster_all_zeros(seeded_app):
    mgr = _make_league_and_manager(
        "SCORE001", "Alice", "aaaaaaaa-1111-2222-3333-444444444444",
    )
    _, scores = manager_scores(mgr.id)
    assert all(v == 0 for v in scores.values())


def test_manager_scores_sums_two_players(seeded_app):
    mgr = _make_league_and_manager(
        "SCORE002", "Bob", "bbbbbbbb-1111-2222-3333-444444444444",
    )
    players = db.session.query(Player).limit(2).all()
    for i, player in enumerate(players):
        db.session.add(HiscoreSnapshot(
            player_id=player.id, snapshot_type="poll",
            snapped_at=datetime(2026, 6, 6, 12, 0, tzinfo=UTC),
            attack_xp=100_000 * (i + 1),
        ))
        db.session.add(RosterEntry(
            manager_id=mgr.id, player_id=player.id, pick_number=i + 1,
            drafted_at=datetime(2026, 5, 31, tzinfo=UTC),
        ))
    db.session.commit()
    _, scores = manager_scores(mgr.id)
    assert scores["combat_xp"] == 300_000  # 100k + 200k


# ── compute_standings ─────────────────────────────────────────────────────────

def _make_six_managers(league_code: str) -> list[Manager]:
    league = League(
        code=league_code,
        commissioner_token=f"{league_code[:8]}-0000-1111-2222-333333333333",
        created_at=datetime(2026, 5, 31, tzinfo=UTC),
    )
    db.session.add(league)
    db.session.flush()
    db.session.add(DraftState(league_id=league.id, current_pick=0))
    managers = []
    for i in range(1, 7):
        m = Manager(
            league_id=league.id,
            name=f"M{i}",
            token=f"{league_code[:4].lower()}{i:04d}-1111-2222-3333-444444444444",
            pick_position=i,
        )
        db.session.add(m)
        managers.append(m)
    db.session.commit()
    return managers


def test_compute_standings_through_day_0_all_zeros(seeded_app):
    managers = _make_six_managers("STAND001")
    standings = compute_standings(managers, through_day=0)
    assert all(r["wins"] == 0 and r["losses"] == 0 for r in standings)


def test_compute_standings_no_positions_all_zeros(seeded_app):
    league = League(
        code="STAND002",
        commissioner_token="stand002-0000-1111-2222-333333333333",
        created_at=datetime(2026, 5, 31, tzinfo=UTC),
    )
    db.session.add(league)
    db.session.flush()
    managers = [
        Manager(league_id=league.id, name=f"M{i}",
                token=f"st2{i:05d}-1111-2222-3333-444444444444")
        for i in range(6)
    ]
    for m in managers:
        db.session.add(m)
    db.session.commit()
    standings = compute_standings(managers, through_day=1)
    assert all(r["wins"] == 0 and r["losses"] == 0 for r in standings)


def test_compute_standings_six_managers_have_records(seeded_app):
    managers = _make_six_managers("STAND003")
    standings = compute_standings(managers, through_day=1)
    assert len(standings) == 6
    total_wins = sum(r["wins"] for r in standings)
    total_losses = sum(r["losses"] for r in standings)
    # Day 1 has 3 matchups, each produces 1 win + 1 loss (or 0+0 for ties)
    # With all-zero scores, all matchups tie → all zeros
    assert total_wins == total_losses


def test_compute_standings_sorted_by_wins(seeded_app):
    managers = _make_six_managers("STAND004")
    players = db.session.query(Player).limit(5).all()
    m1 = next(m for m in managers if m.pick_position == 1)
    for i, player in enumerate(players):
        # Win 4 categories: combat, pvp, bosses, raids (deaths ties at 0)
        db.session.add(HiscoreSnapshot(
            player_id=player.id, snapshot_type="poll",
            snapped_at=datetime(2026, 6, 6, 12, 0, tzinfo=UTC),
            attack_xp=10_000_000,
            pvp_kills=50,
            zulrah=10,
            chambers_of_xeric=5,
        ))
        db.session.add(RosterEntry(
            manager_id=m1.id, player_id=player.id, pick_number=i + 1,
            drafted_at=datetime(2026, 5, 31, tzinfo=UTC),
        ))
    db.session.commit()
    standings = compute_standings(managers, through_day=1)
    assert standings[0]["manager"].id == m1.id
    assert standings[0]["wins"] > 0
