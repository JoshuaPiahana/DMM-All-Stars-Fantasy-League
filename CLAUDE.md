# DMM All Stars 3 — Fantasy League

Fantasy league web app for the OSRS Deadman: All Stars Season 3 event (June 6–15, 2026).
Six managers snake-draft all 30 real-event players and compete head-to-head daily across
7 scoring categories derived from OSRS tournament hiscores.

Target audience: a small group of 6 friends/community members. Must be publicly accessible
online for the community to watch. Event runs for 9 days; the app needs to be live by June 6.

---

## Architecture

### Cloud: AWS

| Service | Role |
|---|---|
| **App Runner** | Hosts the Flask web app (always-on, auto-deploys from ECR) |
| **Lambda + EventBridge Scheduler** | Polls hiscores every 15 min; separate from web app |
| **RDS PostgreSQL** (db.t3.micro) | Database — free tier for 12 months |
| **ECR** | Container registry — GitHub Actions pushes here |
| **Secrets Manager** | DATABASE_URL, commissioner token, any other secrets |
| **ACM** | Origin TLS cert for custom domain (free) |

DNS: Cloudflare Registrar + Cloudflare DNS proxy (free Universal SSL, DDoS protection).
Domain: something like `dmmfantasy.gg` — to be purchased before launch.

### Why these choices
- App Runner stays always-on → no cold-start problems for SSE connections
- Lambda for polling removes APScheduler from the web process; poller is independently
  deployable, testable, and monitorable. Web app becomes read-mostly.
- RDS free tier eliminates DB cost for first 12 months
- No auth infrastructure — league code + manager tokens replace accounts entirely

### CI/CD: GitHub Actions
- **ci.yml**: runs on every push and PR — `ruff check`, `pytest --cov`; fails fast
- **deploy.yml**: runs on merge to `main` — build Docker image, push to ECR,
  App Runner auto-deploys; deploy Lambda zip separately via SAM or AWS CLI

---

## Access Model (No Accounts)

1. Commissioner visits `/create` → enters 6 manager names → receives:
   - **League code** (8-char alphanumeric, e.g. `DMMX7K2F`) — share with everyone
   - **Commissioner token** (UUID) — stored in browser localStorage, unlocks admin panel
2. Each manager visits `/league/DMMX7K2F` → clicks their name → receives a
   **manager token** stored in localStorage. No passwords.
3. Tokens persist in localStorage. A "forget me" link clears it for shared machines.
4. If a manager loses their token, the commissioner can regenerate it from the admin panel.

There is exactly one league per deployment for this event. The league code system exists
to support a clean UX; it is not multi-tenant infrastructure.

---

## Fantasy League Rules (exact spec)

### Format
- 6 managers × 5 players = all 30 players drafted (no one left out)
- Snake draft; pick order randomised at draft start
- Fantasy draft runs alongside/after the real draft stream on May 31, 2026

### Head-to-head matchups
- One matchup per active play day (9 days total, June 6–15 with June 11 world-closed)
- Each day: two managers compare their rosters' **cumulative stats from tournament start**
  across 7 categories. Stats never reset — early performance carries forward.
- **Category win**: higher roster total wins the category. Ties award 0 points to either manager.
- **Matchup win**: manager who wins 4+ of 7 categories wins the day.

### Matchup schedule (pick positions 1–6 assigned randomly at draft start)

| Day | A     | B     | C     |
|-----|-------|-------|-------|
| 1   | 1v2   | 3v4   | 5v6   |
| 2   | 1v3   | 2v5   | 4v6   |
| 3   | 1v4   | 2v6   | 3v5   |
| 4   | 1v5   | 2v4   | 3v6   |
| 5   | 1v6   | 2v3   | 4v5   |
| 6   | 1v2   | 3v4   | 5v6   |
| 7   | 1v3   | 2v5   | 4v6   |
| 8   | 1v4   | 2v6   | 3v5   |
| 9   | 1v5   | 2v4   | 3v6   |

Days 1–5 = full round robin. Days 6–9 = repeat days 1–4.
Day 5 matchups (1v6, 2v3, 4v5) are the only ones without a rematch — intentional.

### Standings
Ranked by matchup wins (W/L). Ties share the higher position — no tiebreaker.

---

## Scoring System (7 Categories)

All values are **current hiscore value minus baseline** (baseline snapshot taken at world
open on June 6, 11:00 UTC). Roster total = sum across all 5 players on the manager's roster.

| # | Category | Formula | Wins by |
|---|----------|---------|---------|
| 1 | **Combat XP** | Atk+Str+Def+Rng+Mage+Prayer+HP XP delta | Most |
| 2 | **PvP Kills** | Bounty Hunter hunter kill count delta | Most |
| 3 | **Bosses** | Sum of (kill delta × boss point weight) across all bosses | Most |
| 4 | **Raids** | CoX + ToB + ToA completion count deltas (1pt each) | Most |
| 5 | **Gathering XP** | Mining+Fishing+WC+Hunter+Farming+Slayer+Thieving XP delta | Most |
| 6 | **Processing XP** | Smithing+Cooking+Fletching+FM+Crafting+Herb+RC+Con XP delta | Most |
| 7 | **Deaths** | Manually entered cumulative death count | Fewest |

### Boss point weights

| Weight | Bosses |
|--------|--------|
| **5**  | Barrows, Wintertodt, Tempoross, Guardians of the Rift, Giant Mole, King Black Dragon, Chaos Fanatic, Chaos Elemental, Scorpia, Crazy Archaeologist, Deranged Archaeologist |
| **10** | Kalphite Queen, Kraken, Thermonuclear Smoke Devil, Sarachnis, Skotizo, Dagannoth Kings (Prime + Rex + Supreme combined), Zalcano |
| **20** | Abyssal Sire, Cerberus, Corporeal Beast, General Graardor, Commander Zilyana, Kree'arra, K'ril Tsutsaroth, Grotesque Guardians |
| **30** | Zulrah, Vorkath, Alchemical Hydra, Phantom Muspah, Nex |

### Raid weights
CoX, ToB, ToA — 1 point per completion regardless of mode. Difficulty variants share the
same hiscores counter.

### Deaths (Category 7)
Not available from hiscores. Commissioner manually enters cumulative death counts per player.
The app must support entry and editing at any time.

---

## Data Sources

### OSRS Tournament Hiscores
`GET https://secure.runescape.com/m=hiscore_oldschool_tournament/index_lite.ws?player=NAME`

Returns CSV: 24 skill rows (rank,level,xp) then activity rows (rank,count).
Skills are in a fixed order; activities follow in a fixed order that includes all boss kills.

**Polling**: Lambda runs every 15 minutes during world-open hours.
**Snapshots**: Dedicated Lambda invocations at world open (11:00 UTC) and world close
(05:00 UTC) each day to mark clean daily boundaries.
**Baseline**: Taken once at event start (June 6, 11:00 UTC) — all displayed stats are
current minus baseline.

### Account names
DMM tournament accounts use team prefixes (e.g. Season 2: `BB Evscape`).
Season 3 prefixes are unknown until event start. The commissioner panel lets the
commissioner set the prefix per team; account names are reconstructed as
`"{prefix} {display_name}"` or can be overridden per player.

### Reference implementation
See `_reference/scraper_poc.py` for the confirmed-working CSV parse logic.
The `ACTIVITY_NAMES` list in that file is incomplete — all boss kill counter names need
to be added in correct hiscores CSV order. Verify against the live endpoint before launch.

---

## Application Pages

| Route | Page | Notes |
|-------|------|-------|
| `/` | Dashboard | standings, today's matchups, live category leaders |
| `/matchup/<day>` | Matchup view | head-to-head with all 7 categories and leaders |
| `/roster/<manager_token>` | Roster | manager's 5 players + individual stat contributions |
| `/player/<id>` | Player detail | individual stats, cumulative totals, chart |
| `/leaderboard` | Leaderboard | all players ranked by any category |
| `/draft` | Draft room | SSE-powered live pick feed |
| `/commissioner` | Admin panel | death entry, prefix config, manual refresh, token reset |

---

## Frontend Design

**Theme**: OSRS dark gold — matches the game's aesthetic, familiar to the community.
Bootstrap 5 for layout. Vanilla JS only (no React/Vue). Plotly.js for stat charts.
Jinja2 templates. No build step.

**CSS variables (use exactly these)**:
```css
--rs-gold:    #ffd700;
--rs-gold-dim:#c8a800;
--rs-dark:    #1a0f00;
--rs-brown:   #3b1f00;
--rs-mid:     #2a1500;
--rs-panel:   #231200;
--rs-border:  #7a5c00;
--rs-text:    #e8d5a0;
--rs-muted:   #9b8a5a;
--rs-green:   #4caf50;
--rs-red:     #ef5350;
--rs-blue:    #42a5f5;
```

Tables: dark brown header with gold column labels, subtle gold row hover.
Cards: dark panel background with gold border and brown header strip.
Buttons: brown background, gold border, gold text — invert on hover.
Rank badges: gold (#1), silver (#2), bronze (#3).

The existing POC's `base.html` CSS is a good starting point for all of the above.

---

## Project Structure (target new app)

```
dmm-fantasy-league/          ← git repo root
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── deploy.yml
├── app/
│   ├── __init__.py          ← create_app() factory
│   ├── config.py            ← Config / TestingConfig / ProductionConfig classes
│   ├── extensions.py        ← db = SQLAlchemy(), migrate = Migrate()
│   ├── models.py            ← all SQLAlchemy models
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── public.py        ← dashboard, matchups, rosters, leaderboard, player
│   │   ├── draft.py         ← draft room + SSE stream
│   │   ├── commissioner.py  ← admin panel endpoints
│   │   └── api.py           ← JSON endpoints consumed by frontend JS
│   ├── services/
│   │   ├── scraper.py       ← hiscores fetch/parse (no Flask dependency)
│   │   ├── scoring.py       ← category calculations, matchup resolution (no Flask)
│   │   └── draft_logic.py   ← snake order, pick validation (no Flask)
│   ├── templates/
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   ├── matchup.html
│   │   ├── roster.html
│   │   ├── player.html
│   │   ├── leaderboard.html
│   │   ├── draft.html
│   │   └── commissioner.html
│   └── static/
│       ├── css/style.css
│       └── js/draft.js      ← SSE client for draft room
├── lambda/
│   ├── handler.py           ← Lambda entry point: imports scraper, writes to DB
│   └── requirements.txt
├── tests/
│   ├── conftest.py          ← app fixture, in-memory SQLite DB, mock scraper
│   ├── test_scoring.py      ← unit tests — pure logic, no DB, no HTTP
│   ├── test_scraper.py      ← parse fixture CSV files, no network calls
│   ├── test_draft_logic.py  ← snake order, pick validation
│   ├── test_routes.py       ← Flask test client integration tests
│   └── fixtures/
│       └── hiscore_sample.txt  ← captured real API response for offline testing
├── migrations/              ← Flask-Migrate / Alembic
├── Dockerfile
├── docker-compose.yml       ← local dev (mounts ./app, hot reload, local Postgres)
├── template.yaml            ← AWS SAM template for Lambda
├── requirements.txt
├── requirements-dev.txt     ← pytest, pytest-cov, ruff, moto (AWS mocking)
└── CLAUDE.md                ← this file
```

---

## Development Rules

### Test-Driven Development — always
Write the test first, then the implementation. No feature code without a failing test first.
This is non-negotiable. The scoring engine and draft logic are the highest-value targets —
get these fully covered before touching routes or templates.

### Code style
- **ruff** for linting and formatting (replaces flake8 + black + isort)
- Type hints on all service layer functions
- No comments unless the WHY is non-obvious (a hidden constraint, a workaround, a gotcha)
- No docstrings beyond a single short line when truly necessary

### Architecture rules
- **App factory**: `create_app(config_object)` in `app/__init__.py`
- **Blueprints**: one per route group; register in `create_app()`
- **Service layer**: `app/services/` modules must have zero Flask imports — pure Python
  functions that accept and return plain dicts/dataclasses. This makes them trivially testable.
- **SQLAlchemy ORM**: always use models, never raw SQL strings. DB-agnostic by default.
- **Config classes**: `Config` base, `TestingConfig` (uses `sqlite:///:memory:`),
  `ProductionConfig` (reads from env vars). Never hardcode secrets.
- **Environment variables**: all secrets via `os.environ`. In production, injected by
  AWS Secrets Manager. Locally, use a `.env` file (gitignored).

### Testing rules
- Services: full unit test coverage — no Flask test client needed, no DB needed
- Routes: Flask test client with seeded in-memory SQLite DB
- Scraper: use fixture CSV files, never hit the real API in tests
- Lambda handler: use `moto` to mock AWS calls if any; otherwise just test the logic
- Target: 80%+ coverage on `app/services/`; smoke tests for critical route paths

### Git workflow
- All work on feature branches; merge to `main` only via PR with passing CI
- `main` = production; every merge deploys
- Commit messages: imperative, concise, explain why not what

---

## Key Unknowns (resolve before June 6)

1. **Season 3 account name prefixes** — announced at event start. Commissioner sets them
   in the admin panel. The scraper uses `"{prefix} {display_name}"` unless overridden.
2. **Real-event team compositions** — revealed on May 31 draft stream. Commissioner maps
   each player to their real_team in the admin panel after the stream.
3. **ACTIVITY_NAMES hiscores order** — the exact CSV row indices for boss kill counters
   need to be verified against the live tournament endpoint. Do this before June 6 by
   fetching a real player from a previous DMM tournament world if one is accessible,
   or on June 6 immediately after world opens.
4. **Bounty Hunter counter reliability** — BH counter is the PvP kill proxy. If it turns
   out not to track kills in tournament worlds, fall back to manual entry (same pattern
   as deaths).

---

## Build Phases

| Phase | Deliverables |
|-------|-------------|
| **1. Scaffold** | GitHub repo, Dockerfile, docker-compose, app factory, empty CI passing |
| **2. Models + migrations** | SQLAlchemy models, Alembic migrations, seeded player list |
| **3. Scoring engine** | `scoring.py` fully unit-tested — category calcs, matchup resolution |
| **4. Scraper + Lambda** | `scraper.py` with fixture tests, Lambda handler, EventBridge template |
| **5. Draft system** | League codes, manager tokens, snake draft logic, SSE stream |
| **6. Frontend** | All 7 pages wired up, OSRS dark gold theme |
| **7. Commissioner panel** | Death entry, prefix config, manual refresh, token management |
| **8. Deploy** | ECR + App Runner live, CI/CD end-to-end, RDS connected |
| **9. Pre-event** | Load real player data, verify ACTIVITY_NAMES, smoke test full flow |

---

## Reference Files

- [`_reference/scraper_poc.py`](_reference/scraper_poc.py) — confirmed-working CSV parse logic; port to `app/services/scraper.py`
- [`_reference/config_poc.py`](_reference/config_poc.py) — player list, team data, skills list; use to seed DB on startup
- [`DMM_AllStars3_Fantasy_ProjectSummary.md`](DMM_AllStars3_Fantasy_ProjectSummary.md) — full original spec
