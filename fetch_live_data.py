"""
fetch_live_data.py
-------------------
Replaces the sample database with REAL data from football-data.org's free
public API (https://www.football-data.org).

Why this API: it has a genuinely free tier, a clean REST interface, and
covers the biggest European leagues (competitions list below). It does
NOT require a credit card. It does NOT include every one of the 10
leagues seeded by generate_sample_data.py (e.g. MLS and Brasileirao
aren't on the free tier) — those will simply be left as sample data
unless you swap in another provider (API-Football on RapidAPI has a
similar free tier and broader league coverage if you want to extend this
script the same way).

Setup:
    1. Create a free account at https://www.football-data.org/client/register
    2. Copy your API token
    3. export FOOTBALL_DATA_API_KEY="your-token-here"
       (or put it in a .env file — see .env.example)
    4. python data/fetch_live_data.py

Free tier limits (as of writing): 10 requests/minute, so this script
paces itself automatically. A full refresh of 5-6 leagues takes a few
minutes — that's expected, not a bug.

Note: the free tier does NOT include detailed match lineups/ratings for
most competitions, so LineupEntry rows (used by the match-center pitch
view) are left as whatever generate_sample_data.py created, or you can
extend fetch_match_details() below once you have a paid tier / a
provider that exposes lineups (e.g. API-Football's `fixtures/lineups`
and `fixtures/players` endpoints follow the same pattern).
"""
import os
import sys
import time
import requests
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db, League, Team, Standing, Player, Match

API_BASE = "https://api.football-data.org/v4"
API_KEY = os.environ.get("FOOTBALL_DATA_API_KEY", "")

# football-data.org competition codes that map onto our seeded leagues.
# (Codes for leagues NOT on their free tier are omitted on purpose.)
COMPETITION_MAP = {
    "PL": "PL",     # Premier League
    "PD": "PD",     # La Liga (Primera Division)
    "SA": "SA",     # Serie A
    "BL1": "BL1",   # Bundesliga
    "FL1": "FL1",   # Ligue 1
    "DED": "DED",   # Eredivisie
    "PPL": "PPL",   # Primeira Liga
    "ELC": "ELC",   # Championship
}

HEADERS = {"X-Auth-Token": API_KEY}


def _normalize_name(name):
    """Strip common club-name suffixes/prefixes so 'Arsenal' and
    'Arsenal FC' (or 'Athletic Club' vs 'Athletic Bilbao') are recognized
    as the same team when matching seed data against the live API."""
    n = name.upper()
    for tok in (" FC", "FC ", " CF", "CF ", " AFC", "AFC ", " SC", "SC ",
                "1. ", " AC", "AC ", " CD", "CD ", " CLUB", "CLUB ",
                " DE FUTEBOL", " FOOTBALL CLUB"):
        n = n.replace(tok, " ")
    return " ".join(n.split())


def api_get(path, params=None):
    resp = requests.get(f"{API_BASE}{path}", headers=HEADERS, params=params, timeout=20)
    if resp.status_code == 429:
        print("  rate limited, waiting 60s…")
        time.sleep(60)
        return api_get(path, params)
    resp.raise_for_status()
    return resp.json()


def sync_competition(league):
    fd_code = COMPETITION_MAP.get(league.code)
    if not fd_code:
        print(f"  skip {league.name} — not available on football-data.org free tier")
        return

    print(f"  fetching {league.name} …")
    data = api_get(f"/competitions/{fd_code}/teams")
    time.sleep(6.5)  # stay under 10 req/min

    fd_id_to_team = {}
    existing_teams = Team.query.filter_by(league_id=league.id).all()
    existing_by_norm = {_normalize_name(t.name): t for t in existing_teams}

    for fd_team in data.get("teams", []):
        name = fd_team["name"]
        short = (fd_team.get("shortName") or name)[:10]

        # Match against the seeded team by normalized name first (handles
        # "Arsenal" vs "Arsenal FC" style differences), falling back to the
        # short name, so we UPDATE existing rows instead of creating dupes.
        team = (existing_by_norm.get(_normalize_name(name))
                or existing_by_norm.get(_normalize_name(short)))

        if not team:
            # Genuinely new team not in our seed list — create it with all
            # required fields set BEFORE the insert to avoid NOT NULL errors.
            team = Team(league_id=league.id, name=name, short_name=short)
            db.session.add(team)
            db.session.flush()  # assigns team.id for the players below

        team.name = name
        team.short_name = short
        team.crest_initials = (fd_team.get("tla") or name[:3]).upper()[:4]
        team.founded = fd_team.get("founded") or team.founded
        venue = fd_team.get("venue")
        if venue:
            team.venue = venue
        fd_id_to_team[fd_team["id"]] = team

        # Squad / players
        Player.query.filter_by(team_id=team.id).delete()
        for sq in fd_team.get("squad", []):
            pos_map = {"Goalkeeper": "GK", "Defence": "DF", "Midfield": "MF", "Offence": "FW"}
            db.session.add(Player(
                team_id=team.id,
                name=sq.get("name", "Unknown"),
                position=pos_map.get(sq.get("position", ""), "MF"),
                shirt_number=sq.get("shirtNumber") or 0,
                nationality=sq.get("nationality") or "",
                age=_age_from_dob(sq.get("dateOfBirth")),
                appearances=0, goals=0, assists=0, yellow_cards=0, red_cards=0,
                minutes=0, avg_rating=6.8, market_value_eur=0,
            ))
    db.session.commit()

    # Standings
    standings_data = api_get(f"/competitions/{fd_code}/standings")
    time.sleep(6.5)
    Standing.query.filter_by(league_id=league.id).delete()
    for table in standings_data.get("standings", []):
        if table.get("type") != "TOTAL":
            continue
        for row in table.get("table", []):
            team = fd_id_to_team.get(row["team"]["id"])
            if not team:
                continue
            db.session.add(Standing(
                league_id=league.id, team_id=team.id, position=row["position"],
                played=row["playedGames"], won=row["won"], drawn=row["draw"], lost=row["lost"],
                goals_for=row["goalsFor"], goals_against=row["goalsAgainst"], points=row["points"],
                form=(row.get("form") or "").replace(",", "")[-5:],
            ))
    db.session.commit()
    print(f"    -> {len(fd_id_to_team)} teams synced")


def _age_from_dob(dob_str):
    if not dob_str:
        return 25
    try:
        dob = datetime.strptime(dob_str[:10], "%Y-%m-%d")
        today = datetime.utcnow()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    except Exception:
        return 25


def main():
    if not API_KEY:
        print("ERROR: set FOOTBALL_DATA_API_KEY (get a free key at "
              "https://www.football-data.org/client/register)")
        sys.exit(1)

    app = create_app()
    with app.app_context():
        leagues = League.query.all()
        if not leagues:
            print("No leagues found — run data/generate_sample_data.py first "
                  "to set up the league/team skeleton, then re-run this script.")
            sys.exit(1)
        for league in leagues:
            sync_competition(league)
    print("\nDone. Restart the Flask app to see live data.")


if __name__ == "__main__":
    main()
