"""Unit tests for draft logic — pure logic, no DB, no Flask (TDD)."""
import uuid

from app.services.draft_logic import (
    generate_league_code,
    generate_token,
    is_draft_complete,
    snake_pick_position,
    validate_pick,
)

# ── generate_league_code ──────────────────────────────────────────────────────

def test_league_code_length():
    assert len(generate_league_code()) == 8


def test_league_code_alphanumeric_uppercase():
    code = generate_league_code()
    assert code.isalnum()
    assert code == code.upper()


def test_league_code_unique():
    codes = {generate_league_code() for _ in range(200)}
    assert len(codes) == 200


# ── generate_token ────────────────────────────────────────────────────────────

def test_token_is_valid_uuid():
    token = generate_token()
    parsed = uuid.UUID(token)
    assert str(parsed) == token


def test_token_unique():
    tokens = {generate_token() for _ in range(100)}
    assert len(tokens) == 100


# ── snake_pick_position ───────────────────────────────────────────────────────

def test_snake_round_1_ascending():
    assert [snake_pick_position(i) for i in range(6)] == [1, 2, 3, 4, 5, 6]


def test_snake_round_2_descending():
    assert [snake_pick_position(6 + i) for i in range(6)] == [6, 5, 4, 3, 2, 1]


def test_snake_round_3_ascending():
    assert [snake_pick_position(12 + i) for i in range(6)] == [1, 2, 3, 4, 5, 6]


def test_snake_round_4_descending():
    assert [snake_pick_position(18 + i) for i in range(6)] == [6, 5, 4, 3, 2, 1]


def test_snake_round_5_ascending():
    assert [snake_pick_position(24 + i) for i in range(6)] == [1, 2, 3, 4, 5, 6]


def test_snake_each_position_gets_5_picks():
    from collections import Counter
    counts = Counter(snake_pick_position(i) for i in range(30))
    for pos in range(1, 7):
        assert counts[pos] == 5, f"position {pos} has {counts[pos]} picks"


def test_snake_pick_0():
    assert snake_pick_position(0) == 1


def test_snake_pick_5():
    assert snake_pick_position(5) == 6


def test_snake_pick_6():
    assert snake_pick_position(6) == 6


def test_snake_pick_11():
    assert snake_pick_position(11) == 1


def test_snake_pick_29():
    assert snake_pick_position(29) == 6


# ── validate_pick ─────────────────────────────────────────────────────────────

def test_validate_pick_not_started():
    err = validate_pick(
        current_pick=0, total_picks=30,
        manager_position=1, started=False, completed=False,
    )
    assert err is not None


def test_validate_pick_already_completed():
    err = validate_pick(
        current_pick=30, total_picks=30,
        manager_position=1, started=True, completed=True,
    )
    assert err is not None


def test_validate_pick_wrong_position():
    # pick 0 belongs to position 1, not 2
    err = validate_pick(
        current_pick=0, total_picks=30,
        manager_position=2, started=True, completed=False,
    )
    assert err is not None


def test_validate_pick_correct_position_round_1():
    err = validate_pick(
        current_pick=0, total_picks=30,
        manager_position=1, started=True, completed=False,
    )
    assert err is None


def test_validate_pick_correct_position_round_2():
    # pick 6 (first of round 2) belongs to position 6
    err = validate_pick(
        current_pick=6, total_picks=30,
        manager_position=6, started=True, completed=False,
    )
    assert err is None


def test_validate_pick_out_of_bounds():
    err = validate_pick(
        current_pick=30, total_picks=30,
        manager_position=1, started=True, completed=False,
    )
    assert err is not None


# ── is_draft_complete ─────────────────────────────────────────────────────────

def test_draft_not_complete_mid():
    assert is_draft_complete(15, 30) is False


def test_draft_not_complete_start():
    assert is_draft_complete(0, 30) is False


def test_draft_complete_all_picks_made():
    assert is_draft_complete(30, 30) is True


def test_draft_not_complete_last_pick():
    assert is_draft_complete(29, 30) is False
