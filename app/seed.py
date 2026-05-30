"""Seed initial player and team data. Idempotent — safe to call on every startup."""

from .extensions import db
from .models import Player, RealTeam

_REAL_TEAMS = [
    {"name": "Odablock Warriors", "color": "#dc2626", "captain": "Odablock"},
    {"name": "Framed Friends",    "color": "#db2777", "captain": "Framed"},
    {"name": "Westham Weasels",   "color": "#ca8a04", "captain": "Westham"},
    {"name": "Dino Nuggets",      "color": "#16a34a", "captain": "Dino"},
    {"name": "Rhys Rhinos",       "color": "#2563eb", "captain": "Rhys"},
    {"name": "Purpp Rebels",      "color": "#9333ea", "captain": "Purpp"},
]

_DRAFTABLE_PLAYERS = [
    "EVScape", "Sick Nerd", "Torvesta", "Greg", "V the Victim", "Lake",
    "C Engineer", "Eliop14", "Skill Specs", "Mika", "Muts", "Skiddler",
    "Pip", "B0aty", "Dubiedobies", "Alfie", "Mr Mammal", "Faux",
    "Gnomonkey", "Synq", "Coxie", "61M", "Raikesy", "MMORPG",
]


def seed_if_empty() -> None:
    if db.session.query(RealTeam).count() > 0:
        return

    team_objects: dict[str, RealTeam] = {}
    for t in _REAL_TEAMS:
        team = RealTeam(name=t["name"], color=t["color"], prefix="")
        db.session.add(team)
        team_objects[t["name"]] = team

    db.session.flush()

    for t in _REAL_TEAMS:
        team = team_objects[t["name"]]
        db.session.add(Player(display_name=t["captain"], is_captain=True, real_team_id=team.id))

    for name in _DRAFTABLE_PLAYERS:
        db.session.add(Player(display_name=name, is_captain=False))

    db.session.commit()
