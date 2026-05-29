"""
REFERENCE ONLY — POC config for DMM All Stars 3.

Useful for porting:
  - ALL_PLAYERS list (30 players, captains flagged, real_team=None until May 31)
  - REAL_TEAMS dict (team names, colors, captains — prefixes TBC at event start)
  - SKILLS list (24 skills in hiscores CSV order)
  - Event dates

DO NOT port SCORING constants — the scoring system changed entirely.
The new system is category-based (7 categories, most wins wins), not points-based.
See CLAUDE.md for the exact new scoring spec.

In the new app, player/team data lives in the database (seeded from config at startup).
Team prefixes are stored in DB and editable by commissioner — not hardcoded.
"""

from datetime import datetime, timezone

EVENT_START = datetime(2026, 6, 6,  11, 0, 0, tzinfo=timezone.utc)
EVENT_END   = datetime(2026, 6, 15, 11, 0, 0, tzinfo=timezone.utc)
FINALE_DATE = datetime(2026, 6, 20, 17, 0, 0, tzinfo=timezone.utc)

HISCORE_BASE_URL = "https://secure.runescape.com/m=hiscore_oldschool_tournament/index_lite.ws"
HISCORE_POLL_MINUTES = 15

SKILLS = [
    "overall", "attack", "defence", "strength", "hitpoints",
    "ranged", "prayer", "magic", "cooking", "woodcutting",
    "fletching", "fishing", "firemaking", "crafting", "smithing",
    "mining", "herblore", "agility", "thieving", "slayer",
    "farming", "runecraft", "hunter", "construction",
]

REAL_TEAMS = {
    "Odablock Warriors": {"color": "#dc2626", "prefix": "",  "captain": "Odablock"},
    "Framed Friends":    {"color": "#db2777", "prefix": "",  "captain": "Framed"},
    "Westham Weasels":   {"color": "#ca8a04", "prefix": "",  "captain": "Westham"},
    "Dino Nuggets":      {"color": "#16a34a", "prefix": "",  "captain": "Dino"},
    "Rhys Rhinos":       {"color": "#2563eb", "prefix": "",  "captain": "Rhys"},
    "Purpp Rebels":      {"color": "#9333ea", "prefix": "",  "captain": "Purpp"},
}
# NOTE: Prefixes left blank — announced at event start, stored in DB.

CAPTAINS = [
    {"display_name": "Odablock",  "real_team": "Odablock Warriors", "is_captain": True},
    {"display_name": "Framed",    "real_team": "Framed Friends",    "is_captain": True},
    {"display_name": "Westham",   "real_team": "Westham Weasels",   "is_captain": True},
    {"display_name": "Dino",      "real_team": "Dino Nuggets",      "is_captain": True},
    {"display_name": "Rhys",      "real_team": "Rhys Rhinos",       "is_captain": True},
    {"display_name": "Purpp",     "real_team": "Purpp Rebels",      "is_captain": True},
]

DRAFTABLE_PLAYERS = [
    {"display_name": "EVScape",      "real_team": None, "is_captain": False},
    {"display_name": "Sick Nerd",    "real_team": None, "is_captain": False},
    {"display_name": "Torvesta",     "real_team": None, "is_captain": False},
    {"display_name": "Greg",         "real_team": None, "is_captain": False},
    {"display_name": "V the Victim", "real_team": None, "is_captain": False},
    {"display_name": "Lake",         "real_team": None, "is_captain": False},
    {"display_name": "C Engineer",   "real_team": None, "is_captain": False},
    {"display_name": "Eliop14",      "real_team": None, "is_captain": False},
    {"display_name": "Skill Specs",  "real_team": None, "is_captain": False},
    {"display_name": "Mika",         "real_team": None, "is_captain": False},
    {"display_name": "Muts",         "real_team": None, "is_captain": False},
    {"display_name": "Skiddler",     "real_team": None, "is_captain": False},
    {"display_name": "Pip",          "real_team": None, "is_captain": False},
    {"display_name": "B0aty",        "real_team": None, "is_captain": False},
    {"display_name": "Dubiedobies",  "real_team": None, "is_captain": False},
    {"display_name": "Alfie",        "real_team": None, "is_captain": False},
    {"display_name": "Mr Mammal",    "real_team": None, "is_captain": False},
    {"display_name": "Faux",         "real_team": None, "is_captain": False},
    {"display_name": "Gnomonkey",    "real_team": None, "is_captain": False},
    {"display_name": "Synq",         "real_team": None, "is_captain": False},
    {"display_name": "Coxie",        "real_team": None, "is_captain": False},
    {"display_name": "61M",          "real_team": None, "is_captain": False},
    {"display_name": "Raikesy",      "real_team": None, "is_captain": False},
    {"display_name": "MMORPG",       "real_team": None, "is_captain": False},
]

ALL_PLAYERS = CAPTAINS + DRAFTABLE_PLAYERS
assert len(ALL_PLAYERS) == 30
