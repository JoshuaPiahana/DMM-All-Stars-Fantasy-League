"""Scoring engine — pure Python, zero Flask dependencies."""

from __future__ import annotations

# ── Category field definitions ────────────────────────────────────────────────

_COMBAT_SKILLS = [
    "attack_xp", "defence_xp", "strength_xp", "hitpoints_xp",
    "ranged_xp", "prayer_xp", "magic_xp",
]

_GATHERING_SKILLS = [
    "mining_xp", "fishing_xp", "woodcutting_xp", "hunter_xp",
    "farming_xp", "slayer_xp", "thieving_xp",
]

_PROCESSING_SKILLS = [
    "smithing_xp", "cooking_xp", "fletching_xp", "firemaking_xp",
    "crafting_xp", "herblore_xp", "runecraft_xp", "construction_xp",
]

_RAID_FIELDS = ["chambers_of_xeric", "theatre_of_blood", "tombs_of_amascut"]

_BOSS_WEIGHTS: dict[str, int] = {
    # weight 5
    "barrows_chests": 5, "wintertodt": 5, "tempoross": 5,
    "guardians_of_the_rift": 5, "giant_mole": 5, "king_black_dragon": 5,
    "chaos_fanatic": 5, "chaos_elemental": 5, "scorpia": 5,
    "crazy_archaeologist": 5, "deranged_archaeologist": 5,
    # weight 10
    "kalphite_queen": 10, "kraken": 10, "thermonuclear_smoke_devil": 10,
    "sarachnis": 10, "skotizo": 10,
    "dagannoth_prime": 10, "dagannoth_rex": 10, "dagannoth_supreme": 10,
    "zalcano": 10,
    # weight 20
    "abyssal_sire": 20, "cerberus": 20, "corporeal_beast": 20,
    "general_graardor": 20, "commander_zilyana": 20, "kreearra": 20,
    "kril_tsutsaroth": 20, "grotesque_guardians": 20,
    # weight 30
    "zulrah": 30, "vorkath": 30, "alchemical_hydra": 30,
    "phantom_muspah": 30, "nex": 30,
}

# ── Matchup schedule (positions 1-6 assigned randomly at draft start) ─────────

_SCHEDULE: dict[int, list[tuple[int, int]]] = {
    1: [(1, 2), (3, 4), (5, 6)],
    2: [(1, 3), (2, 5), (4, 6)],
    3: [(1, 4), (2, 6), (3, 5)],
    4: [(1, 5), (2, 4), (3, 6)],
    5: [(1, 6), (2, 3), (4, 5)],
    6: [(1, 2), (3, 4), (5, 6)],
    7: [(1, 3), (2, 5), (4, 6)],
    8: [(1, 4), (2, 6), (3, 5)],
    9: [(1, 5), (2, 4), (3, 6)],
}

# All numeric fields that appear in a stat dict
ALL_STAT_FIELDS: list[str] = (
    _COMBAT_SKILLS + _GATHERING_SKILLS + _PROCESSING_SKILLS
    + _RAID_FIELDS + list(_BOSS_WEIGHTS)
    + ["overall_xp", "agility_xp", "pvp_kills", "deaths_cumulative"]
)

# Display names for the 7 scoring categories (in matchup order)
CATEGORY_LABELS: dict[str, str] = {
    "combat_xp":     "Combat XP",
    "pvp_kills":     "PvP Kills",
    "bosses":        "Boss Points",
    "raids":         "Raid Completions",
    "gathering_xp":  "Gathering XP",
    "processing_xp": "Processing XP",
    "deaths":        "Deaths",
}

CATEGORY_ORDER: list[str] = list(CATEGORY_LABELS.keys())


# ── Public API ────────────────────────────────────────────────────────────────

def compute_delta(current: dict, baseline: dict) -> dict:
    """Return current − baseline for every stat field, clamped to 0."""
    return {
        field: max(0, current.get(field, 0) - baseline.get(field, 0))
        for field in ALL_STAT_FIELDS
    }


def sum_roster(player_deltas: list[dict]) -> dict:
    """Sum per-player deltas across a full roster."""
    totals: dict[str, int] = {field: 0 for field in ALL_STAT_FIELDS}
    for delta in player_deltas:
        for field in ALL_STAT_FIELDS:
            totals[field] += delta.get(field, 0)
    return totals


def compute_category_scores(totals: dict) -> dict[str, int]:
    """Compute all 7 category scores from roster totals."""
    return {
        "combat_xp":    sum(totals.get(f, 0) for f in _COMBAT_SKILLS),
        "pvp_kills":    totals.get("pvp_kills", 0),
        "bosses":       sum(totals.get(boss, 0) * w for boss, w in _BOSS_WEIGHTS.items()),
        "raids":        sum(totals.get(f, 0) for f in _RAID_FIELDS),
        "gathering_xp": sum(totals.get(f, 0) for f in _GATHERING_SKILLS),
        "processing_xp":sum(totals.get(f, 0) for f in _PROCESSING_SKILLS),
        "deaths":       totals.get("deaths_cumulative", 0),
    }


def resolve_matchup(scores_a: dict, scores_b: dict) -> dict:
    """
    Compare two managers' category scores.

    Returns a dict with:
      category_results: {category: {a, b, winner}}
      wins_a, wins_b: int
      matchup_winner: "a" | "b" | None
    """
    category_results: dict[str, dict] = {}
    wins_a = wins_b = 0

    for category in ("combat_xp", "pvp_kills", "bosses", "raids",
                     "gathering_xp", "processing_xp", "deaths"):
        val_a = scores_a.get(category, 0)
        val_b = scores_b.get(category, 0)

        if category == "deaths":
            # Fewer deaths wins
            if val_a < val_b:
                winner: str | None = "a"
                wins_a += 1
            elif val_b < val_a:
                winner = "b"
                wins_b += 1
            else:
                winner = None
        else:
            if val_a > val_b:
                winner = "a"
                wins_a += 1
            elif val_b > val_a:
                winner = "b"
                wins_b += 1
            else:
                winner = None

        category_results[category] = {"a": val_a, "b": val_b, "winner": winner}

    matchup_winner: str | None
    if wins_a >= 4:
        matchup_winner = "a"
    elif wins_b >= 4:
        matchup_winner = "b"
    else:
        matchup_winner = None

    return {
        "category_results": category_results,
        "wins_a": wins_a,
        "wins_b": wins_b,
        "matchup_winner": matchup_winner,
    }


def matchup_pairs(day: int) -> list[tuple[int, int]]:
    """Return the 3 (pos_a, pos_b) matchup pairs for a given play day (1–9)."""
    if day not in _SCHEDULE:
        raise ValueError(f"day must be 1–9, got {day}")
    return _SCHEDULE[day]
