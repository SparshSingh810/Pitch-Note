"""
PitchNote — a FotMob-style football data app.
Flask + SQLAlchemy (SQLite) + server-rendered Jinja templates.
"""
import os
from flask import Flask, render_template, abort, request
from models import db, League, Team, Standing, Player, Match, LineupEntry

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(BASE_DIR, 'data', 'pitchnote.db')}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    register_routes(app)
    return app


def register_routes(app):

    @app.context_processor
    def inject_globals():
        return {"all_leagues": League.query.order_by(League.name).all()}

    @app.route("/")
    def home():
        leagues = League.query.order_by(League.name).all()
        featured = leagues[0] if leagues else None
        recent_matches = (Match.query.order_by(Match.kickoff.desc()).limit(8).all())
        top_rated = (Player.query.order_by(Player.avg_rating.desc()).limit(6).all())
        top_scorers = (Player.query.order_by(Player.goals.desc()).limit(6).all())
        standings_preview = featured.standings()[:6] if featured else []
        return render_template("index.html", leagues=leagues, featured=featured,
                                recent_matches=recent_matches, top_rated=top_rated,
                                top_scorers=top_scorers, standings_preview=standings_preview)

    @app.route("/league/<code>")
    def league_page(code):
        league = League.query.filter_by(code=code).first_or_404()
        tab = request.args.get("tab", "table")
        standings = league.standings()
        matches = Match.query.filter_by(league_id=league.id).order_by(Match.kickoff.desc()).all()
        top_scorers = (Player.query.join(Team).filter(Team.league_id == league.id)
                       .order_by(Player.goals.desc()).limit(10).all())
        top_assists = (Player.query.join(Team).filter(Team.league_id == league.id)
                        .order_by(Player.assists.desc()).limit(10).all())
        top_rated = (Player.query.join(Team).filter(Team.league_id == league.id)
                     .order_by(Player.avg_rating.desc()).limit(10).all())
        return render_template("league.html", league=league, standings=standings, matches=matches,
                                top_scorers=top_scorers, top_assists=top_assists, top_rated=top_rated,
                                tab=tab)

    @app.route("/team/<int:team_id>")
    def team_page(team_id):
        team = Team.query.get_or_404(team_id)
        squad = Player.query.filter_by(team_id=team.id).order_by(
            db.case((Player.position == "GK", 0), (Player.position == "DF", 1),
                    (Player.position == "MF", 2), (Player.position == "FW", 3), else_=4),
            Player.shirt_number).all()
        standing = team.standing()
        recent = (Match.query.filter((Match.home_team_id == team.id) | (Match.away_team_id == team.id))
                  .order_by(Match.kickoff.desc()).limit(6).all())
        return render_template("team.html", team=team, squad=squad, standing=standing, recent=recent)

    @app.route("/player/<int:player_id>")
    def player_page(player_id):
        player = Player.query.get_or_404(player_id)
        entries = (LineupEntry.query.filter_by(player_id=player.id)
                   .order_by(LineupEntry.id.desc()).limit(10).all())
        return render_template("player.html", player=player, entries=entries)

    @app.route("/match/<int:match_id>")
    def match_page(match_id):
        match = Match.query.get_or_404(match_id)
        home_lineup = (LineupEntry.query.filter_by(match_id=match.id, team_id=match.home_team_id,
                                                     is_starting=True).all())
        away_lineup = (LineupEntry.query.filter_by(match_id=match.id, team_id=match.away_team_id,
                                                     is_starting=True).all())
        home_subs = (LineupEntry.query.filter_by(match_id=match.id, team_id=match.home_team_id,
                                                   is_starting=False).all())
        away_subs = (LineupEntry.query.filter_by(match_id=match.id, team_id=match.away_team_id,
                                                   is_starting=False).all())
        top_performers = match.top_performers(3)
        return render_template("match.html", match=match, home_lineup=home_lineup, away_lineup=away_lineup,
                                home_subs=home_subs, away_subs=away_subs, top_performers=top_performers)

    @app.route("/search")
    def search():
        q = request.args.get("q", "").strip()
        teams, players = [], []
        if q:
            teams = Team.query.filter(Team.name.ilike(f"%{q}%")).limit(10).all()
            players = Player.query.filter(Player.name.ilike(f"%{q}%")).limit(10).all()
        return render_template("search.html", q=q, teams=teams, players=players)

    @app.errorhandler(404)
    def not_found(e):
        return render_template("404.html"), 404


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
