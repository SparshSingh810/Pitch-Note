"""
generate_sample_data.py
------------------------
Builds a ready-to-browse SQLite database for the app WITHOUT needing any
internet access or API key.

- League and club names are real (top 10 leagues worldwide).
- Player names, ages, stats, standings, and match ratings are
  PROCEDURALLY GENERATED placeholder data (seeded random, so results are
  stable across runs) — they are NOT real current statistics.

Run `python data/fetch_live_data.py` afterwards (with a free API key) to
overwrite this with real live data from football-data.org.

Usage:
    python data/generate_sample_data.py
"""
import random
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db, League, Team, Standing, Player, Match, LineupEntry

random.seed(42)

# ---------------------------------------------------------------------------
# 10 real top-flight leagues with their real clubs (2025/26 style rosters).
# ---------------------------------------------------------------------------
LEAGUES = [
    {
        "code": "PL", "name": "Premier League", "country": "England", "logo": "🏴",
        "color": "#3D195B",
        "teams": ["Arsenal", "Manchester City", "Liverpool", "Chelsea", "Manchester United",
                  "Tottenham Hotspur", "Newcastle United", "Aston Villa", "Brighton & Hove Albion",
                  "West Ham United", "Brentford", "Crystal Palace", "Fulham", "Wolverhampton Wanderers",
                  "Everton", "Nottingham Forest", "Bournemouth", "Burnley", "Sunderland", "Leeds United"],
    },
    {
        "code": "PD", "name": "La Liga", "country": "Spain", "logo": "🇪🇸",
        "color": "#EE8707",
        "teams": ["Real Madrid", "Barcelona", "Atletico Madrid", "Athletic Bilbao", "Real Sociedad",
                  "Real Betis", "Villarreal", "Valencia", "Sevilla", "Girona", "Celta Vigo",
                  "Osasuna", "Getafe", "Rayo Vallecano", "Mallorca", "Alaves", "Las Palmas",
                  "Espanyol", "Levante", "Elche"],
    },
    {
        "code": "SA", "name": "Serie A", "country": "Italy", "logo": "🇮🇹",
        "color": "#008FD7",
        "teams": ["Inter Milan", "AC Milan", "Juventus", "Napoli", "Roma", "Atalanta", "Lazio",
                  "Fiorentina", "Bologna", "Torino", "Udinese", "Monza", "Genoa", "Verona",
                  "Cagliari", "Empoli", "Lecce", "Sassuolo", "Parma", "Como"],
    },
    {
        "code": "BL1", "name": "Bundesliga", "country": "Germany", "logo": "🇩🇪",
        "color": "#D3010C",
        "teams": ["Bayern Munich", "Bayer Leverkusen", "Borussia Dortmund", "RB Leipzig",
                  "Eintracht Frankfurt", "VfB Stuttgart", "Freiburg", "Union Berlin", "Wolfsburg",
                  "Borussia Monchengladbach", "Mainz 05", "Werder Bremen", "Augsburg", "Hoffenheim",
                  "Heidenheim", "St Pauli", "Bochum", "Holstein Kiel"],
    },
    {
        "code": "FL1", "name": "Ligue 1", "country": "France", "logo": "🇫🇷",
        "color": "#091C3E",
        "teams": ["Paris Saint-Germain", "Marseille", "Monaco", "Lille", "Lyon", "Nice",
                  "Lens", "Rennes", "Reims", "Toulouse", "Strasbourg", "Nantes", "Montpellier",
                  "Brest", "Le Havre", "Angers", "Auxerre", "Saint-Etienne"],
    },
    {
        "code": "DED", "name": "Eredivisie", "country": "Netherlands", "logo": "🇳🇱",
        "color": "#FF6E00",
        "teams": ["Ajax", "PSV Eindhoven", "Feyenoord", "AZ Alkmaar", "FC Twente", "FC Utrecht",
                  "Vitesse", "Heerenveen", "Sparta Rotterdam", "Go Ahead Eagles", "NEC Nijmegen",
                  "Fortuna Sittard", "Willem II", "Groningen", "Heracles Almelo", "PEC Zwolle",
                  "Volendam", "Excelsior"],
    },
    {
        "code": "PPL", "name": "Primeira Liga", "country": "Portugal", "logo": "🇵🇹",
        "color": "#046A38",
        "teams": ["Benfica", "Porto", "Sporting CP", "Braga", "Vitoria Guimaraes", "Gil Vicente",
                  "Famalicao", "Moreirense", "Santa Clara", "Boavista", "Rio Ave", "Casa Pia",
                  "Estoril", "Arouca", "Farense", "Nacional", "Estrela Amadora", "AVS"],
    },
    {
        "code": "ELC", "name": "Championship", "country": "England", "logo": "🏴",
        "color": "#1D428A",
        "teams": ["Leicester City", "Southampton", "Ipswich Town", "West Bromwich Albion",
                  "Norwich City", "Middlesbrough", "Coventry City", "Hull City", "Preston North End",
                  "Bristol City", "Watford", "Millwall", "Sheffield Wednesday", "Swansea City",
                  "Cardiff City", "Stoke City", "Blackburn Rovers", "Queens Park Rangers",
                  "Plymouth Argyle", "Sheffield United"],
    },
    {
        "code": "BSA", "name": "Brasileirao Serie A", "country": "Brazil", "logo": "🇧🇷",
        "color": "#FFCC29",
        "teams": ["Flamengo", "Palmeiras", "Sao Paulo", "Corinthians", "Fluminense", "Botafogo",
                  "Gremio", "Internacional", "Atletico Mineiro", "Cruzeiro", "Bahia", "Fortaleza",
                  "Vasco da Gama", "Santos", "Bragantino", "Athletico Paranaense", "Criciuma",
                  "Cuiaba", "Vitoria", "Juventude"],
    },
    {
        "code": "MLS", "name": "Major League Soccer", "country": "USA", "logo": "🇺🇸",
        "color": "#000000",
        "teams": ["Inter Miami", "LAFC", "LA Galaxy", "Seattle Sounders", "Columbus Crew",
                  "New York City FC", "New York Red Bulls", "Atlanta United", "Philadelphia Union",
                  "FC Cincinnati", "Orlando City", "Nashville SC", "Austin FC", "Charlotte FC",
                  "Real Salt Lake", "Portland Timbers", "Minnesota United", "Chicago Fire"],
    },
]

NATIONALITIES = ["England", "Spain", "France", "Germany", "Italy", "Portugal", "Brazil",
                  "Argentina", "Netherlands", "Belgium", "Croatia", "Nigeria", "Ivory Coast",
                  "Senegal", "Morocco", "Ghana", "USA", "Japan", "South Korea", "Colombia",
                  "Uruguay", "Denmark", "Norway", "Sweden", "Austria", "Poland", "Serbia"]

FIRST_NAMES = ["Lucas", "Mateo", "Diego", "Marco", "Luca", "Kai", "Noah", "Leon", "Jamal",
               "Andre", "Bruno", "Rafael", "Hugo", "Tom", "Jack", "Harry", "Oscar", "Theo",
               "Elias", "Mohamed", "Youssef", "Karim", "Victor", "Nathan", "Ethan", "Gabriel",
               "Miguel", "Pedro", "Joao", "Antoine", "Kevin", "Erik", "Sven", "Jonas", "Fabio",
               "Adrian", "Ivan", "Milan", "Dario", "Nico", "Alex", "Sam", "Ben", "Ryan", "Cole"]

LAST_NAMES = ["Silva", "Santos", "Fernandez", "Garcia", "Rossi", "Bianchi", "Muller", "Schmidt",
              "Dubois", "Bernard", "Van Dijk", "De Jong", "Johnson", "Smith", "Williams", "Brown",
              "Costa", "Pereira", "Almeida", "Diallo", "Toure", "Mensah", "Traore", "Coulibaly",
              "Petrov", "Kovac", "Nowak", "Kowalski", "Andersson", "Nilsson", "Hansen", "Larsen",
              "Okafor", "Adeyemi", "Suarez", "Martinez", "Lopez", "Moreno", "Rodrigues", "Carvalho"]

POSITIONS = [("GK", 3), ("DF", 8), ("MF", 8), ("FW", 6)]
FORMATIONS = ["4-3-3", "4-2-3-1", "3-5-2", "4-4-2", "3-4-3"]


def gen_name():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


def make_squad(team, top_flight_boost=0):
    players = []
    number = 1
    for pos, count in POSITIONS:
        for _ in range(count):
            base_rating = random.uniform(6.2, 7.0) + top_flight_boost
            player = Player(
                team_id=team.id,
                name=gen_name(),
                position=pos,
                shirt_number=number,
                nationality=random.choice(NATIONALITIES),
                age=random.randint(18, 35),
                appearances=random.randint(5, 30),
                goals=random.randint(0, 18) if pos in ("FW", "MF") else random.randint(0, 3),
                assists=random.randint(0, 12) if pos in ("FW", "MF") else random.randint(0, 4),
                yellow_cards=random.randint(0, 8),
                red_cards=random.choice([0, 0, 0, 0, 1]),
                minutes=random.randint(400, 2700),
                avg_rating=round(min(base_rating, 9.2), 2),
                market_value_eur=random.randint(500_000, 120_000_000) - (0 if pos != "GK" else 40_000_000),
            )
            players.append(player)
            number += 1
    return players


def simulate_table(league_id, teams):
    """Simulate a partial season to produce plausible standings + form."""
    stats = {t.id: {"played": 0, "won": 0, "drawn": 0, "lost": 0, "gf": 0, "ga": 0, "pts": 0, "form": []}
              for t in teams}
    games_played_target = random.randint(14, 22)

    team_ids = [t.id for t in teams]
    for _ in range(games_played_target):
        random.shuffle(team_ids)
        for i in range(0, len(team_ids) - 1, 2):
            h, a = team_ids[i], team_ids[i + 1]
            hg = random.choices(range(0, 5), weights=[15, 30, 25, 18, 12])[0]
            ag = random.choices(range(0, 5), weights=[20, 30, 24, 16, 10])[0]
            stats[h]["played"] += 1
            stats[a]["played"] += 1
            stats[h]["gf"] += hg
            stats[h]["ga"] += ag
            stats[a]["gf"] += ag
            stats[a]["ga"] += hg
            if hg > ag:
                stats[h]["won"] += 1
                stats[a]["lost"] += 1
                stats[h]["pts"] += 3
                stats[h]["form"].append("W")
                stats[a]["form"].append("L")
            elif hg < ag:
                stats[a]["won"] += 1
                stats[h]["lost"] += 1
                stats[a]["pts"] += 3
                stats[a]["form"].append("W")
                stats[h]["form"].append("L")
            else:
                stats[h]["drawn"] += 1
                stats[a]["drawn"] += 1
                stats[h]["pts"] += 1
                stats[a]["pts"] += 1
                stats[h]["form"].append("D")
                stats[a]["form"].append("D")

    ranked = sorted(team_ids, key=lambda tid: (stats[tid]["pts"], stats[tid]["gf"] - stats[tid]["ga"]), reverse=True)
    standings = []
    for pos, tid in enumerate(ranked, start=1):
        s = stats[tid]
        standings.append(Standing(
            league_id=league_id, team_id=tid, position=pos,
            played=s["played"], won=s["won"], drawn=s["drawn"], lost=s["lost"],
            goals_for=s["gf"], goals_against=s["ga"], points=s["pts"],
            form="".join(s["form"][-5:]),
        ))
    return standings


def build_lineup(match, home, away, home_players, away_players):
    def slot_players(players):
        gk = [p for p in players if p.position == "GK"][:1]
        df = [p for p in players if p.position == "DF"][:4]
        mf = [p for p in players if p.position == "MF"][:4]
        fw = [p for p in players if p.position == "FW"][:2]
        starters = gk + df + mf + fw
        subs = [p for p in players if p not in starters][:7]
        return starters, subs

    for team, players, is_home in ((home, home_players, True), (away, away_players, False)):
        starters, subs = slot_players(players)
        y_base = 8 if is_home else 92
        y_dir = 1 if is_home else -1
        rows = {"GK": 1, "DF": 2, "MF": 3, "FW": 4}
        row_counts = {}
        for p in starters:
            row_counts[p.position] = row_counts.get(p.position, 0) + 1
        row_index = {}
        for p in starters:
            idx = row_index.get(p.position, 0)
            row_index[p.position] = idx + 1
            count = row_counts[p.position]
            x = (idx + 1) * (100 / (count + 1))
            y = y_base + y_dir * (rows[p.position] * 18)
            rating = round(random.uniform(5.8, 9.1), 1)
            db.session.add(LineupEntry(
                match_id=match.id, team_id=team.id, player_id=p.id, is_starting=True,
                pos_x=round(x, 1), pos_y=round(y, 1), position_label=p.position,
                rating=rating, goals=random.choices([0, 1, 2], weights=[85, 12, 3])[0] if p.position in ("FW", "MF") else 0,
                assists=random.choices([0, 1], weights=[88, 12])[0],
                yellow_card=random.random() < 0.12, red_card=random.random() < 0.02,
            ))
        for p in subs:
            db.session.add(LineupEntry(
                match_id=match.id, team_id=team.id, player_id=p.id, is_starting=False,
                pos_x=0, pos_y=0, position_label=p.position,
                rating=round(random.uniform(5.8, 7.6), 1),
                goals=0, assists=0, yellow_card=False, red_card=False,
            ))


def main():
    app = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()

        for li, ldata in enumerate(LEAGUES):
            boost = 0.35 if li < 5 else 0.0  # top-5 leagues get slightly higher quality ratings
            league = League(code=ldata["code"], name=ldata["name"], country=ldata["country"],
                             logo=ldata["logo"], color=ldata["color"])
            db.session.add(league)
            db.session.flush()

            teams = []
            for tname in ldata["teams"]:
                initials = "".join([w[0] for w in tname.split()[:3]]).upper()[:3]
                team = Team(league_id=league.id, name=tname, short_name=tname[:3].upper(),
                            crest_initials=initials, primary_color=ldata["color"],
                            founded=random.randint(1880, 1998),
                            venue=f"{tname.split()[0]} Stadium")
                db.session.add(team)
                teams.append(team)
            db.session.flush()

            for team in teams:
                squad = make_squad(team, top_flight_boost=boost)
                db.session.add_all(squad)
            db.session.flush()

            standings = simulate_table(league.id, teams)
            db.session.add_all(standings)

            # Create a handful of sample matches (with full lineups + ratings)
            random.shuffle(teams)
            num_matches = 5 if li < 5 else 3
            for m in range(num_matches):
                home, away = teams[m * 2 % len(teams)], teams[(m * 2 + 1) % len(teams)]
                if home.id == away.id:
                    continue
                hg = random.choices(range(0, 5), weights=[15, 30, 25, 18, 12])[0]
                ag = random.choices(range(0, 5), weights=[20, 30, 24, 16, 10])[0]
                match = Match(
                    league_id=league.id, home_team_id=home.id, away_team_id=away.id,
                    home_score=hg, away_score=ag, status="FT", minute=90,
                    matchday=random.randint(10, 24),
                    kickoff=datetime.utcnow() - timedelta(days=random.randint(0, 6), hours=random.randint(0, 23)),
                    home_formation=random.choice(FORMATIONS), away_formation=random.choice(FORMATIONS),
                    venue=home.venue,
                )
                db.session.add(match)
                db.session.flush()
                build_lineup(match, home, away, Player.query.filter_by(team_id=home.id).all(),
                             Player.query.filter_by(team_id=away.id).all())

            db.session.commit()
            print(f"  seeded {league.name:<25} {len(teams)} teams")

        db.session.commit()
        print("\nDatabase built successfully.")
        print(f"Leagues: {League.query.count()} | Teams: {Team.query.count()} | "
              f"Players: {Player.query.count()} | Matches: {Match.query.count()}")


if __name__ == "__main__":
    main()
