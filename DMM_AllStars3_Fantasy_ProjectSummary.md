# DMM All Stars 3 Fantasy League — Project Summary

## What We're Building
A fantasy league web app for the OSRS **Deadman: All Stars Season 3** event, modelled on NBA-style head-to-head fantasy leagues. Six managers draft individual OSRS players onto their roster and compete against each other daily based on those players' cumulative in-game stats. The app should be publicly available online for the community.

---

## The Real Event (context)
- **Event runs:** June 6–15, 2026 (9 active play days — world closed June 11 as midweek break)
- **World hours:** Closed 05:00–11:00 UTC daily, open 18 hours/day
- **Finale:** June 20, 2026 live at Rosemont Theatre, Chicago — **excluded from fantasy scoring**
- **Format:** 30 players total — 6 team captains + 24 draftable players, split into 6 teams of 5
- **Real-event teams and captains:**
  - Odablock Warriors (Red) — Captain: Odablock
  - Framed Friends (Pink) — Captain: Framed
  - Westham Weasels (Yellow) — Captain: Westham
  - Dino Nuggets (Green) — Captain: Dino
  - Rhys Rhinos (Blue) — Captain: Rhys
  - Purpp Rebels (Purple) — Captain: Purpp
- **Draftable players (24):** EVScape, Sick Nerd, Torvesta, Greg, V the Victim, Lake, C Engineer, Eliop14, Skill Specs, Mika, Muts, Skiddler, Pip, B0aty, Dubiedobies, Alfie, Mr Mammal, Faux, Gnomonkey, Synq, Coxie, 61M, Raikesy, MMORPG
- **Real-event draft:** Livestream on May 31, 2026 — team compositions revealed then

---

## Fantasy League Rules

### Managers & Rosters
- Exactly **6 managers** required
- **5 players per manager** (6 × 5 = all 30 players drafted, no one left out)
- **Snake draft**, pick order randomised at draft start
- Fantasy draft runs alongside/after the real draft stream on May 31

### Match Format
- **Head-to-head daily** — each manager plays one opponent per day
- **9 matchups** across the event (one per active play day)
- Each day, two managers compare their rosters' **cumulative stats from tournament start** across 7 scoring categories
- Whoever leads more categories wins the day
- **Category wins:** 1 point per category to the leader — **ties award zero points to either manager**
- Manager who wins 4 or more of the 7 categories wins the matchup

### Schedule
Pick order numbers 1–6 are assigned randomly at draft time. The schedule is:

| Day | Matchup A | Matchup B | Matchup C |
|-----|-----------|-----------|-----------|
| 1   | 1 vs 2    | 3 vs 4    | 5 vs 6    |
| 2   | 1 vs 3    | 2 vs 5    | 4 vs 6    |
| 3   | 1 vs 4    | 2 vs 6    | 3 vs 5    |
| 4   | 1 vs 5    | 2 vs 4    | 3 vs 6    |
| 5   | 1 vs 6    | 2 vs 3    | 4 vs 5    |
| 6   | 1 vs 2    | 3 vs 4    | 5 vs 6    |
| 7   | 1 vs 3    | 2 vs 5    | 4 vs 6    |
| 8   | 1 vs 4    | 2 vs 6    | 3 vs 5    |
| 9   | 1 vs 5    | 2 vs 4    | 3 vs 6    |

Days 1–5 are a full round robin (every manager plays every other manager once). Days 6–9 repeat days 1–4. The day 5 pairings (1v6, 2v3, 4v5) are the only matchups that never get a rematch — this is intentional and accepted.

### Standings & Tiebreakers
- Managers are ranked by total matchup wins (W/L record)
- If two or more managers are tied on wins, they **share the higher position** — no tiebreaker, both/all get the same placement

### Finale
The June 20 finale is excluded from fantasy scoring entirely.

---

## Scoring System

### The 7 Categories

All stats are **cumulative from tournament start**. Each day's matchup compares total accumulated stats at that point — stats never reset. A manager whose players had a strong day 1 carries that advantage forward into all future matchups.

| # | Category | What counts | Wins by |
|---|----------|-------------|---------|
| 1 | **Combat XP** | Attack + Strength + Defence + Ranged + Magic + Prayer + Hitpoints XP | Most XP |
| 2 | **PvP Kills** | Bounty Hunter kill counter | Most kills |
| 3 | **Bosses** | Weighted boss kill points (see table below) | Most points |
| 4 | **Raids** | Total raid completions across CoX, ToB, ToA | Most completions |
| 5 | **Gathering XP** | Mining + Fishing + Woodcutting + Hunter + Farming + Slayer + Thieving XP | Most XP |
| 6 | **Processing XP** | Smithing + Cooking + Fletching + Firemaking + Crafting + Herblore + Runecraft + Construction XP | Most XP |
| 7 | **Deaths** | Total deaths (manual entry) | Fewest deaths |

### Boss Point Weights

Each boss kill adds the following points to the roster's cumulative Boss score:

| Points per kill | Bosses |
|----------------|--------|
| **5**  | Barrows, Wintertodt, Tempoross, Guardians of the Rift, Giant Mole, King Black Dragon, Chaos Fanatic, Chaos Elemental, Scorpia, Crazy Archaeologist, Deranged Archaeologist |
| **10** | Kalphite Queen, Kraken, Thermonuclear Smoke Devil, Sarachnis, Skotizo, Dagannoth Kings (Prime + Rex + Supreme combined), Zalcano |
| **20** | Abyssal Sire, Cerberus, Corporeal Beast, General Graardor, Commander Zilyana, Kree'arra, K'ril Tsutsaroth, Grotesque Guardians |
| **30** | Zulrah, Vorkath, Alchemical Hydra, Phantom Muspah, Nex |

### Raid Point Weights

Each raid completion (regardless of difficulty mode) is worth **1 point**:
- Chambers of Xeric — 1 point per completion
- Theatre of Blood — 1 point per completion
- Tombs of Amascut — 1 point per completion

The hiscores tracks these as separate counters; difficulty variants (CM, HM, expert) share the same counter and are not distinguished.

---

## Data Sources

### Primary: OSRS Tournament Hiscores
- **Endpoint:** `https://secure.runescape.com/m=hiscore_oldschool_tournament/index_lite.ws?player=NAME`
- Returns CSV with rank, level, and XP for all 24 skills, plus rank and kill count for all activities (Bounty Hunter, clues, bosses, raids)
- **Polling:** Every 15 minutes during the event
- **Snapshots:** Clean daily snapshots at world open (11:00 UTC) and world close (05:00 UTC)
- **Account names:** DMM tournament accounts use team prefixes (e.g. Season 2 used `BB Evscape`). Season 3 prefixes unknown until event starts — must be configurable by commissioner
- **Precedent:** Community developer built an identical scraper for Season 2 at https://github.com/valtterivalo/dmm-allstars2-hiscores using this same endpoint — confirmed working

### Skills tracked (24)
Overall, Attack, Defence, Strength, Hitpoints, Ranged, Prayer, Magic, Cooking, Woodcutting, Fletching, Fishing, Firemaking, Crafting, Smithing, Mining, Herblore, Agility, Thieving, Slayer, Farming, Runecraft, Hunter, Construction

### Activities tracked (relevant ones)
- Bounty Hunter hunter (PvP kills proxy)
- All boss kill counters (see boss list above)
- Chambers of Xeric, Theatre of Blood, Tombs of Amascut completion counters

### Category 7: Deaths
- **Not available** from hiscores
- Commissioner manually enters cumulative death counts per player
- App must support manual entry and editing of death counts at any time

---

## Application Requirements

### Core Features
- **Draft room** — snake draft interface, randomised pick order, live picks visible to all managers
- **Dashboard** — current standings, today's matchups, live category leaders
- **Matchup view** — day-by-day head-to-head breakdown showing all 7 categories and who leads each
- **Roster page** — each manager's 5 players with individual stat contributions
- **Player detail page** — individual player stats, cumulative totals, contribution breakdown
- **Leaderboard** — all players ranked by any stat category
- **Commissioner panel** — manual death entry, player name/prefix configuration, manual data refresh trigger

### Data Architecture
- Baseline snapshot taken at event start (world open on June 6, 11:00 UTC)
- All displayed stats = current hiscore value minus baseline value
- Polling runs every 15 minutes via background scheduler
- Deaths stored separately in database, updated manually

### Scoring Calculation
- Per-player cumulative stats computed from baseline delta
- Boss points: sum across all bosses of (kill count delta × point weight)
- Raid points: sum across CoX + ToB + ToA of completion count delta
- Roster totals: sum across all 5 players on the manager's roster
- Category winner: higher roster total (or lower for deaths)
- Matchup winner: manager with more category wins out of 7 (ties = 0 points to either)

---

## Tech Stack (from proof of concept — rebuild cleanly)
- **Backend:** Python Flask
- **Database:** SQLite
- **Frontend:** Bootstrap 5 + Plotly.js, RuneScape dark gold theme
- **Scheduling:** APScheduler for background polling
- **Deployment:** Must be publicly accessible online (Render or similar)

## Existing Proof of Concept
A working Flask skeleton exists at:
`C:\Users\Froober\Documents\Claude\Projects\DMM All Stars Fantasy League\fantasy-league\`

Files: `config.py`, `database.py`, `scraper.py`, `scoring.py`, `app.py`, `templates/` (7 pages), `requirements.txt`, `run.py`

**Treat as reference only.** The scoring system has fundamentally changed — rebuild from scratch using this document as the spec. The scraper logic and hiscores endpoint handling are worth reusing.

---

## What's Still Unknown Until Event Starts
- Season 3 team name prefixes for in-game account names (configurable by commissioner)
- Whether the Bounty Hunter counter reliably tracks kills in DMM tournament worlds (use as best available proxy, fall back to manual if not)
- Exact real-event team compositions (revealed May 31 draft stream)
