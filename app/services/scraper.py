"""
Hiscores scraper — pure Python, zero Flask dependencies.

ACTIVITY_NAMES is derived from the OSRS JSON hiscores endpoint
(m=hiscore_oldschool/index_lite.json) which returns named activity IDs.

IMPORTANT: Verify against the live tournament endpoint on June 6, 2026:
  GET https://secure.runescape.com/m=hiscore_oldschool_tournament/index_lite.ws?player=<name>

Key uncertainties to verify on June 6:
  - Whether the tournament endpoint includes Sailing (skill 24).
    The parser auto-detects: if row 24 has 3 comma-separated values it is
    treated as a skill row, otherwise as activity[0].
  - Whether Bounty Hunter - Hunter (activity id=3) is the correct PvP kill
    proxy, or whether legacy BH (activity id=5) is used in tournament worlds.
  - Whether Rifts closed (activity id=17) correctly tracks Guardians of the
    Rift completions in a tournament context.
  - Whether any activities at the start (Grid Points id=0, Deadman Points id=2)
    are absent from the tournament endpoint, shifting all activity indices.
"""

from __future__ import annotations

import logging
from typing import Any

import requests

log = logging.getLogger(__name__)

TIMEOUT = 10

TOURNAMENT_URL = "https://secure.runescape.com/m=hiscore_oldschool_tournament/index_lite.ws"
REGULAR_URL = "https://secure.runescape.com/m=hiscore_oldschool/index_lite.ws"

# 25 skills in CSV row order (Sailing added as id=24 in the current API).
# If the tournament endpoint omits Sailing, the parser auto-detects this.
SKILLS = [
    "overall", "attack", "defence", "strength", "hitpoints",
    "ranged", "prayer", "magic", "cooking", "woodcutting",
    "fletching", "fishing", "firemaking", "crafting", "smithing",
    "mining", "herblore", "agility", "thieving", "slayer",
    "farming", "runecraft", "hunter", "construction",
    "sailing",  # id=24 — may be absent in tournament world; auto-detected
]

# 89 activities in CSV row order, derived from the regular hiscores JSON endpoint.
# Names match HiscoreSnapshot model columns where applicable.
# "rifts_closed" is remapped to "guardians_of_the_rift" after parsing.
# "bounty_hunter_hunter" is remapped to "pvp_kills" after parsing.
ACTIVITY_NAMES = [
    "grid_points",                       # 0
    "league_points",                     # 1
    "deadman_points",                    # 2
    "bounty_hunter_hunter",              # 3  → remapped to pvp_kills
    "bounty_hunter_rogue",               # 4
    "bounty_hunter_hunter_legacy",       # 5
    "bounty_hunter_rogue_legacy",        # 6
    "clue_scrolls_all",                  # 7
    "clue_scrolls_beginner",             # 8
    "clue_scrolls_easy",                 # 9
    "clue_scrolls_medium",               # 10
    "clue_scrolls_hard",                 # 11
    "clue_scrolls_elite",                # 12
    "clue_scrolls_master",               # 13
    "lms_rank",                          # 14
    "pvp_arena_rank",                    # 15
    "soul_wars_zeal",                    # 16
    "rifts_closed",                      # 17  → remapped to guardians_of_the_rift
    "colosseum_glory",                   # 18
    "collections_logged",                # 19
    "abyssal_sire",                      # 20
    "alchemical_hydra",                  # 21
    "amoxliatl",                         # 22
    "araxxor",                           # 23
    "artio",                             # 24
    "barrows_chests",                    # 25
    "brutus",                            # 26
    "bryophyta",                         # 27
    "callisto",                          # 28
    "calvarion",                         # 29
    "cerberus",                          # 30
    "chambers_of_xeric",                 # 31
    "chambers_of_xeric_challenge_mode",  # 32
    "chaos_elemental",                   # 33
    "chaos_fanatic",                     # 34
    "commander_zilyana",                 # 35
    "corporeal_beast",                   # 36
    "crazy_archaeologist",               # 37
    "dagannoth_prime",                   # 38
    "dagannoth_rex",                     # 39
    "dagannoth_supreme",                 # 40
    "deranged_archaeologist",            # 41
    "doom_of_mokhaiotl",                 # 42
    "duke_sucellus",                     # 43
    "general_graardor",                  # 44
    "giant_mole",                        # 45
    "grotesque_guardians",               # 46
    "hespori",                           # 47
    "kalphite_queen",                    # 48
    "king_black_dragon",                 # 49
    "kraken",                            # 50
    "kreearra",                          # 51
    "kril_tsutsaroth",                   # 52
    "lunar_chests",                      # 53
    "mimic",                             # 54
    "nex",                               # 55
    "nightmare",                         # 56
    "phosanis_nightmare",                # 57
    "obor",                              # 58
    "phantom_muspah",                    # 59
    "sarachnis",                         # 60
    "scorpia",                           # 61
    "scurrius",                          # 62
    "shellbane_gryphon",                 # 63
    "skotizo",                           # 64
    "sol_heredit",                       # 65
    "spindel",                           # 66
    "tempoross",                         # 67
    "the_gauntlet",                      # 68
    "the_corrupted_gauntlet",            # 69
    "the_hueycoatl",                     # 70
    "the_leviathan",                     # 71
    "the_royal_titans",                  # 72
    "the_whisperer",                     # 73
    "theatre_of_blood",                  # 74
    "theatre_of_blood_hard_mode",        # 75
    "thermonuclear_smoke_devil",         # 76
    "tombs_of_amascut",                  # 77
    "tombs_of_amascut_expert_mode",      # 78
    "tzkal_zuk",                         # 79
    "tztok_jad",                         # 80
    "vardorvis",                         # 81
    "venenatis",                         # 82
    "vetion",                            # 83
    "vorkath",                           # 84
    "wintertodt",                        # 85
    "yama",                              # 86
    "zalcano",                           # 87
    "zulrah",                            # 88
]


def build_account_name(display_name: str, prefix: str) -> str | None:
    """Return the in-game DMM account name, or None if the prefix is not yet known."""
    if not prefix:
        return None
    return f"{prefix} {display_name}"


def parse_hiscore_csv(text: str) -> dict[str, Any]:
    """
    Parse a raw tournament hiscores CSV response into a stat dict.

    Auto-detects whether Sailing (skill id=24) is present by checking whether
    CSV row 24 has 3 comma-separated values (skill format: rank,level,xp) or
    2 values (activity format: rank,count).
    """
    lines = text.strip().split("\n")
    data: dict[str, Any] = {}

    # Auto-detect skill count: sailing present iff row 24 has 3 fields
    num_skills = 25 if (len(lines) > 24 and len(lines[24].split(",")) == 3) else 24
    skills_to_parse = SKILLS[:num_skills]

    for i, skill in enumerate(skills_to_parse):
        if i >= len(lines):
            break
        parts = lines[i].split(",")
        if len(parts) < 3:
            continue
        try:
            data[f"{skill}_xp"] = max(0, int(parts[2]))
            data[f"{skill}_level"] = max(0, int(parts[1]))
        except ValueError:
            pass

    activity_start = num_skills
    for j, activity in enumerate(ACTIVITY_NAMES):
        idx = activity_start + j
        if idx >= len(lines):
            break
        parts = lines[idx].split(",")
        if len(parts) < 2:
            continue
        try:
            count = int(parts[1])
            data[activity] = max(0, count) if count >= 0 else 0
        except ValueError:
            pass

    # Remap to model column names
    data["pvp_kills"] = data.pop("bounty_hunter_hunter", 0)
    data["guardians_of_the_rift"] = data.pop("rifts_closed", 0)

    return data


def fetch_player(account_name: str, base_url: str = TOURNAMENT_URL) -> dict[str, Any] | None:
    """
    Fetch and parse hiscores for one player.
    Returns None on 404 (player not found) or on request error.
    """
    try:
        resp = requests.get(base_url, params={"player": account_name}, timeout=TIMEOUT)
        if resp.status_code == 404:
            log.debug("Player not found: %s", account_name)
            return None
        resp.raise_for_status()
    except requests.RequestException as exc:
        log.warning("Hiscores request failed for %s: %s", account_name, exc)
        return None

    return parse_hiscore_csv(resp.text)
