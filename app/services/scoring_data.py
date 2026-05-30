"""DB-backed scoring helpers — bridges ORM models and the pure scoring engine."""
from __future__ import annotations

from datetime import UTC, date, datetime

from app.extensions import db
from app.models import Death, HiscoreSnapshot, Manager, RosterEntry
from app.services.scoring import (
    ALL_STAT_FIELDS,
    compute_category_scores,
    compute_delta,
    matchup_pairs,
    resolve_matchup,
    sum_roster,
)

_EVENT_DATE_TO_DAY: dict[date, int] = {
    date(2026, 6, 6): 1,
    date(2026, 6, 7): 2,
    date(2026, 6, 8): 3,
    date(2026, 6, 9): 4,
    date(2026, 6, 10): 5,
    date(2026, 6, 12): 6,
    date(2026, 6, 13): 7,
    date(2026, 6, 14): 8,
    date(2026, 6, 15): 9,
}


def current_event_day() -> int | None:
    """Return today's event day (1–9) or None if today is not an event day."""
    return _EVENT_DATE_TO_DAY.get(datetime.now(UTC).date())


def _zero_dict() -> dict:
    return {f: 0 for f in ALL_STAT_FIELDS}


def _snap_to_dict(snap: HiscoreSnapshot) -> dict:
    return {f: getattr(snap, f, 0) for f in ALL_STAT_FIELDS}


def player_delta(player_id: int) -> dict:
    """Current stats minus baseline for a player. All zeros if no snapshots."""
    current = (
        db.session.query(HiscoreSnapshot)
        .filter_by(player_id=player_id)
        .order_by(HiscoreSnapshot.snapped_at.desc())
        .first()
    )
    if not current:
        return _zero_dict()
    baseline = (
        db.session.query(HiscoreSnapshot)
        .filter(
            HiscoreSnapshot.player_id == player_id,
            HiscoreSnapshot.snapshot_type == "baseline",
        )
        .order_by(HiscoreSnapshot.snapped_at.asc())
        .first()
    )
    delta = compute_delta(
        _snap_to_dict(current),
        _snap_to_dict(baseline) if baseline else _zero_dict(),
    )
    # Deaths are manually entered — override snapshot value with latest entry
    latest_death = (
        db.session.query(Death)
        .filter_by(player_id=player_id)
        .order_by(Death.recorded_at.desc())
        .first()
    )
    if latest_death:
        delta["deaths_cumulative"] = latest_death.cumulative_count
    return delta


def manager_scores(manager_id: int) -> tuple[dict, dict]:
    """(roster_totals, category_scores) for a manager using current snapshot data."""
    entries = db.session.query(RosterEntry).filter_by(manager_id=manager_id).all()
    if not entries:
        zero = _zero_dict()
        return zero, compute_category_scores(zero)
    deltas = [player_delta(e.player_id) for e in entries]
    totals = sum_roster(deltas)
    return totals, compute_category_scores(totals)


def compute_standings(managers: list[Manager], through_day: int) -> list[dict]:
    """W/L standings through `through_day` using current snapshot data."""
    pos_to_mgr: dict[int, Manager] = {
        m.pick_position: m for m in managers if m.pick_position is not None
    }
    record: dict[int, dict] = {
        m.id: {"manager": m, "wins": 0, "losses": 0, "ties": 0}
        for m in managers
    }
    if not pos_to_mgr or through_day < 1:
        return sorted(record.values(), key=lambda r: (-r["wins"], r["losses"]))

    scores_by_id: dict[int, dict] = {
        m.id: manager_scores(m.id)[1] for m in managers
    }

    for day in range(1, through_day + 1):
        try:
            pairs = matchup_pairs(day)
        except ValueError:
            break
        for pos_a, pos_b in pairs:
            mgr_a = pos_to_mgr.get(pos_a)
            mgr_b = pos_to_mgr.get(pos_b)
            if not mgr_a or not mgr_b:
                continue
            result = resolve_matchup(scores_by_id[mgr_a.id], scores_by_id[mgr_b.id])
            winner = result["matchup_winner"]
            if winner == "a":
                record[mgr_a.id]["wins"] += 1
                record[mgr_b.id]["losses"] += 1
            elif winner == "b":
                record[mgr_b.id]["wins"] += 1
                record[mgr_a.id]["losses"] += 1
            else:
                record[mgr_a.id]["ties"] += 1
                record[mgr_b.id]["ties"] += 1

    return sorted(record.values(), key=lambda r: (-r["wins"], r["losses"]))
