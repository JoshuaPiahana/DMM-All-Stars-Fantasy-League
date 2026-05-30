"""
Scraper tests.

Offline tests use tests/fixtures/hiscore_sample.txt and never hit the network.
Live tests (marked `live`) hit the real OSRS regular hiscores API.
Run live tests with:  pytest -m live --tb=short

Fixture layout (114 rows = 25 skills + 89 activities):
  skill rows 0-24: attack_xp=5M, defence=4M, strength=6M, hitpoints=7M,
                   ranged=3M, prayer=2M, magic=4.5M,
                   mining=1M, fishing=800K, woodcutting=1.2M, hunter=500K,
                   farming=600K, slayer=2M, thieving=700K,
                   smithing=400K, cooking=900K, fletching=350K, firemaking=1.1M,
                   crafting=450K, herblore=800K, runecraft=600K, construction=300K
  activity[3]  (bounty_hunter_hunter)  → pvp_kills = 15
  activity[17] (rifts_closed)          → guardians_of_the_rift = 200
  activity[25] (barrows_chests)        = 50
  activity[31] (chambers_of_xeric)     = 10
  activity[38-40] (dagannoth kings)    = 15 each
  activity[48] (kalphite_queen)        = 20
  activity[55] (nex)                   = 8
  activity[74] (theatre_of_blood)      = 5
  activity[77] (tombs_of_amascut)      = 3
  activity[84] (vorkath)               = 80
  activity[85] (wintertodt)            = 30
  activity[88] (zulrah)                = 100
"""

from pathlib import Path

import pytest

from app.services.scraper import (
    ACTIVITY_NAMES,
    REGULAR_URL,
    TOURNAMENT_URL,
    build_account_name,
    fetch_player,
    parse_hiscore_csv,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "hiscore_sample.txt"


@pytest.fixture
def sample_csv() -> str:
    return FIXTURE_PATH.read_text()


@pytest.fixture
def parsed(sample_csv) -> dict:
    return parse_hiscore_csv(sample_csv)


# ── build_account_name ────────────────────────────────────────────────────────

def test_build_account_name_with_prefix():
    assert build_account_name("EVScape", "BB") == "BB EVScape"


def test_build_account_name_no_prefix_returns_none():
    assert build_account_name("EVScape", "") is None


def test_build_account_name_prefix_with_spaces():
    assert build_account_name("Odablock", "OB") == "OB Odablock"


# ── parse_hiscore_csv — skill XP ──────────────────────────────────────────────

def test_parse_attack_xp(parsed):
    assert parsed["attack_xp"] == 5_000_000


def test_parse_defence_xp(parsed):
    assert parsed["defence_xp"] == 4_000_000


def test_parse_strength_xp(parsed):
    assert parsed["strength_xp"] == 6_000_000


def test_parse_hitpoints_xp(parsed):
    assert parsed["hitpoints_xp"] == 7_000_000


def test_parse_ranged_xp(parsed):
    assert parsed["ranged_xp"] == 3_000_000


def test_parse_prayer_xp(parsed):
    assert parsed["prayer_xp"] == 2_000_000


def test_parse_magic_xp(parsed):
    assert parsed["magic_xp"] == 4_500_000


def test_parse_gathering_skills(parsed):
    assert parsed["mining_xp"] == 1_000_000
    assert parsed["fishing_xp"] == 800_000
    assert parsed["woodcutting_xp"] == 1_200_000
    assert parsed["hunter_xp"] == 500_000
    assert parsed["farming_xp"] == 600_000
    assert parsed["slayer_xp"] == 2_000_000
    assert parsed["thieving_xp"] == 700_000


def test_parse_processing_skills(parsed):
    assert parsed["smithing_xp"] == 400_000
    assert parsed["cooking_xp"] == 900_000
    assert parsed["fletching_xp"] == 350_000
    assert parsed["firemaking_xp"] == 1_100_000
    assert parsed["crafting_xp"] == 450_000
    assert parsed["herblore_xp"] == 800_000
    assert parsed["runecraft_xp"] == 600_000
    assert parsed["construction_xp"] == 300_000


# ── parse_hiscore_csv — activities ────────────────────────────────────────────

def test_parse_pvp_kills(parsed):
    assert parsed["pvp_kills"] == 15


def test_bounty_hunter_hunter_key_not_present(parsed):
    """bounty_hunter_hunter must be remapped; original key should not exist."""
    assert "bounty_hunter_hunter" not in parsed


def test_parse_guardians_of_the_rift(parsed):
    assert parsed["guardians_of_the_rift"] == 200


def test_rifts_closed_key_not_present(parsed):
    """rifts_closed must be remapped; original key should not exist."""
    assert "rifts_closed" not in parsed


def test_parse_barrows_chests(parsed):
    assert parsed["barrows_chests"] == 50


def test_parse_chambers_of_xeric(parsed):
    assert parsed["chambers_of_xeric"] == 10


def test_parse_dagannoth_kings(parsed):
    assert parsed["dagannoth_prime"] == 15
    assert parsed["dagannoth_rex"] == 15
    assert parsed["dagannoth_supreme"] == 15


def test_parse_kalphite_queen(parsed):
    assert parsed["kalphite_queen"] == 20


def test_parse_nex(parsed):
    assert parsed["nex"] == 8


def test_parse_theatre_of_blood(parsed):
    assert parsed["theatre_of_blood"] == 5


def test_parse_tombs_of_amascut(parsed):
    assert parsed["tombs_of_amascut"] == 3


def test_parse_vorkath(parsed):
    assert parsed["vorkath"] == 80


def test_parse_wintertodt(parsed):
    assert parsed["wintertodt"] == 30


def test_parse_zulrah(parsed):
    assert parsed["zulrah"] == 100


def test_parse_negative_values_clamped_to_zero(parsed):
    """Unranked entries (-1,-1) should produce 0 not -1."""
    assert parsed.get("abyssal_sire", 0) == 0
    assert parsed.get("kraken", 0) == 0


# ── Activity list completeness ────────────────────────────────────────────────

def test_activity_names_contains_all_scoring_bosses():
    """Every boss in the scoring model must be findable in the activity list."""
    scoring_bosses = [
        "barrows_chests", "wintertodt", "tempoross", "guardians_of_the_rift",
        "giant_mole", "king_black_dragon", "chaos_fanatic", "chaos_elemental",
        "scorpia", "crazy_archaeologist", "deranged_archaeologist",
        "kalphite_queen", "kraken", "thermonuclear_smoke_devil", "sarachnis",
        "skotizo", "dagannoth_prime", "dagannoth_rex", "dagannoth_supreme",
        "zalcano", "abyssal_sire", "cerberus", "corporeal_beast",
        "general_graardor", "commander_zilyana", "kreearra", "kril_tsutsaroth",
        "grotesque_guardians", "zulrah", "vorkath", "alchemical_hydra",
        "phantom_muspah", "nex",
    ]
    # guardians_of_the_rift comes from rifts_closed (remapped)
    remapped = {"guardians_of_the_rift"}
    in_activities_or_remapped = set(ACTIVITY_NAMES) | remapped | {"rifts_closed"}
    missing = [b for b in scoring_bosses if b not in in_activities_or_remapped]
    assert missing == [], f"Bosses missing from ACTIVITY_NAMES: {missing}"


def test_activity_names_contains_raids():
    assert "chambers_of_xeric" in ACTIVITY_NAMES
    assert "theatre_of_blood" in ACTIVITY_NAMES
    assert "tombs_of_amascut" in ACTIVITY_NAMES


# ── Sailing auto-detection ────────────────────────────────────────────────────

def test_parse_detects_sailing_present(sample_csv):
    """Fixture has 25 skill rows — sailing should be parsed."""
    parsed = parse_hiscore_csv(sample_csv)
    assert parsed.get("sailing_xp", 0) == 2_000_000


def test_parse_handles_24_skill_csv():
    """If sailing is absent (24-skill CSV), activities still map correctly."""
    fixture = FIXTURE_PATH.read_text().splitlines()
    # Remove the sailing row (row 24) to simulate a pre-sailing tournament endpoint
    lines_no_sailing = fixture[:24] + fixture[25:]
    csv_text = "\n".join(lines_no_sailing)
    parsed = parse_hiscore_csv(csv_text)
    # With 24 skills, activity[3] = bounty_hunter_hunter is at row 27
    # pvp_kills should still be 15 IF the activity indices didn't shift
    # (they should remain correct because auto-detection adjusts activity_start)
    assert parsed.get("pvp_kills", 0) == 15
    assert parsed.get("barrows_chests", 0) == 50


# ── fetch_player (offline: bad responses) ────────────────────────────────────

def test_fetch_player_returns_none_on_404(requests_mock):
    requests_mock.get(TOURNAMENT_URL, status_code=404)
    result = fetch_player("Unknown Player")
    assert result is None


def test_fetch_player_returns_none_on_request_error(requests_mock):
    import requests as _req
    requests_mock.get(TOURNAMENT_URL, exc=_req.exceptions.ConnectionError("timeout"))
    result = fetch_player("Any Player")
    assert result is None


def test_fetch_player_parses_valid_response(requests_mock, sample_csv):
    requests_mock.get(TOURNAMENT_URL, text=sample_csv)
    result = fetch_player("Test Player")
    assert result is not None
    assert result["attack_xp"] == 5_000_000
    assert result["pvp_kills"] == 15


# ── Live tests (require internet, run with: pytest -m live) ───────────────────

@pytest.mark.live
def test_live_regular_hiscores_fetch_known_player():
    """
    Verifies the scraper works against the live regular OSRS hiscores.
    Confirms ACTIVITY_NAMES ordering is still correct.
    Woox is a well-known player with documented boss KC.
    """
    result = fetch_player("Woox", base_url=REGULAR_URL)
    assert result is not None, "Woox not found on regular hiscores"

    # Woox is known to have substantial KC in these bosses
    assert result["vorkath"] > 0, "Woox should have Vorkath KC"
    assert result["theatre_of_blood"] > 0, "Woox should have ToB KC"
    assert result["zulrah"] > 0, "Woox should have Zulrah KC"

    # PvP kills remapping worked
    assert "pvp_kills" in result
    assert "bounty_hunter_hunter" not in result

    # Rifts closed remapping worked
    assert "guardians_of_the_rift" in result
    assert "rifts_closed" not in result

    # Skill XP parsing sanity check
    assert result["attack_xp"] > 10_000_000, "Woox has 99 attack"


@pytest.mark.live
def test_live_tournament_hiscores_currently_404():
    """
    Tournament world is not open yet (opens June 6, 2026).
    This test documents expected current behaviour.
    Once the event starts, this test should be removed or updated.
    """
    result = fetch_player("Odablock", base_url=TOURNAMENT_URL)
    assert result is None, (
        "Expected 404 — if this fails, the tournament world may be open! "
        "Update ACTIVITY_NAMES verification and remove this test."
    )
