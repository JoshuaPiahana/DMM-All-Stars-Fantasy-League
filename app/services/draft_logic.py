"""Draft logic — pure Python, zero Flask/DB dependencies."""
from __future__ import annotations

import random
import string
import uuid


def generate_league_code() -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=8))


def generate_token() -> str:
    return str(uuid.uuid4())


def snake_pick_position(pick_number: int, num_managers: int = 6) -> int:
    """Return the 1-based pick position for a 0-indexed pick number (snake order)."""
    round_num = pick_number // num_managers
    offset = pick_number % num_managers
    if round_num % 2 == 0:
        return offset + 1
    return num_managers - offset


def validate_pick(
    current_pick: int,
    total_picks: int,
    manager_position: int,
    started: bool,
    completed: bool,
) -> str | None:
    """Return an error string if the pick is invalid, else None."""
    if not started:
        return "Draft has not started"
    if completed:
        return "Draft is complete"
    if current_pick >= total_picks:
        return "All picks have been made"
    if manager_position != snake_pick_position(current_pick):
        return f"Not your turn — waiting for position {snake_pick_position(current_pick)}"
    return None


def is_draft_complete(current_pick: int, total_picks: int) -> bool:
    return current_pick >= total_picks
