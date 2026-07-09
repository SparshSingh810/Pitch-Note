# PitchNote ⚽

A FotMob-style football (soccer) stats site — live-style standings, squads,
player ratings, and a match center with a visual pitch lineup — built with
**Python (Flask) + SQLite** and zero JavaScript frameworks. Runs anywhere,
deploys anywhere, no paid services required.

![status](https://img.shields.io/badge/status-ready--to--run-22D39A)
![python](https://img.shields.io/badge/python-3.10%2B-5B6EF5)

## Features

- **10 top-flight leagues**: Premier League, La Liga, Serie A, Bundesliga,
  Ligue 1, Eredivisie, Primeira Liga, Championship, Brasileirão, MLS
- **Full standings tables** with form guide, qualification/relegation rails
- **League stat leaders**: top scorers, top assists, highest-rated players
- **Team pages**: squad list, season stats, recent results
- **Player profiles**: appearances, goals, assists, cards, market value,
  match-by-match ratings
- **Match center**: score, formations, a visual pitch with player dots and
  color-coded ratings, substitutes, top performers
- **Search** across teams and players
- Dark, distinctive "match-day" UI — no template-default look, built with a
  signature color-coded rating system used consistently everywhere

## ⚠️ About the data

This repo ships in two modes:

| Mode | What it is | How to get it |
|---|---|---|
| **Sample data** (default) | Real league & club names, but procedurally generated squads/stats/ratings — lets the whole site run instantly with zero setup | Already included; regenerate with `python data/generate_sample_data.py` |
| **Live data** | Real squads and real standings pulled from [football-data.org](https://www.football-data.org)'s free API | Get a free API key, then run `python data/fetch_live_data.py` |

The free football-data.org tier covers 8 of the 10 leagues here (not
MLS or Brasileirão) and doesn't expose detailed lineups/ratings, so the
match-center pitch view stays on sample data even in live mode unless you
wire in a richer provider (see comments in `data/fetch_live_data.py` —
API-Football on RapidAPI is a good next step and follows the same pattern).

## Quickstart

```bash
# 1. Clone and enter the project
git clone <your-fork-url>
cd pitchnote

# 2. Create a virtual environment
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Generate the database (sample data, instant, no API key needed)
python data/generate_sample_data.py

# 5. Run it
python app.py
```

Open **http://localhost:5000**.

### Switching to live data

```bash
export FOOTBALL_DATA_API_KEY="your-free-key-here"   # Windows: set FOOTBALL_DATA_API_KEY=...
python data/fetch_live_data.py
python app.py
```

## Project structure

```
pitchnote/
├── app.py                     # Flask app + routes
├── models.py                  # SQLAlchemy models
├── requirements.txt
├── data/
│   ├── generate_sample_data.py   # builds the instant-demo database
│   ├── fetch_live_data.py        # pulls real data from football-data.org
│   └── pitchnote.db              # generated (gitignored)
├── templates/                 # Jinja2 templates
│   ├── base.html, index.html, league.html, team.html,
│   │   player.html, match.html, search.html, 404.html
│   └── _macros.html           # shared crest / rating-ring macros
└── static/
    ├── css/style.css          # design system + all page styles
    └── js/main.js
```

## Deploying

**Render / Railway / Fly.io** (all have free tiers):
1. Push this repo to GitHub
2. Create a new Web Service pointing at the repo
3. Build command: `pip install -r requirements.txt && python data/generate_sample_data.py`
4. Start command: `gunicorn app:app`

**Docker** (optional — add your own `Dockerfile` from `python:3.12-slim`,
`pip install -r requirements.txt`, run `data/generate_sample_data.py` at
build time, then `CMD ["gunicorn","-b","0.0.0.0:8000","app:app"]`).

A `Procfile` is included for Heroku-style platforms.

## Extending it

- **More leagues/data**: add a `LEAGUES` entry in `data/generate_sample_data.py`,
  or extend `COMPETITION_MAP` in `data/fetch_live_data.py` if your provider
  covers it.
- **Real lineups & live ratings**: API-Football's `fixtures/lineups` and
  `fixtures/players` endpoints map cleanly onto the `LineupEntry` model —
  swap `fetch_live_data.py`'s HTTP calls for those and keep everything else.
- **Live/in-play matches**: add a scheduler (e.g. `APScheduler`) that polls
  your data provider every minute and updates `Match.status`/`minute`.
- **Auth/favorites**: the models are plain SQLAlchemy — add a `User` model
  and a join table for "favorite teams" whenever you're ready.

## Tech stack

Flask · Flask-SQLAlchemy · SQLite · Jinja2 · vanilla CSS/JS (no build step)

## License

MIT — do whatever you like with it.
