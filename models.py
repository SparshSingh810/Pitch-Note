"""
Database models for PitchNote (FotMob-style football data app).

Kept intentionally simple (SQLite + SQLAlchemy) so the whole project
runs with zero external services. Swap SQLALCHEMY_DATABASE_URI in
app.py if you want Postgres/MySQL later — nothing else changes.
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class League(db.Model):
    __tablename__ = "leagues"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False)   # e.g. "PL"
    name = db.Column(db.String(80), nullable=False)                # Premier League
    country = db.Column(db.String(60), nullable=False)
    season = db.Column(db.String(20), default="2025/26")
    tier = db.Column(db.Integer, default=1)
    logo = db.Column(db.String(10), default="⚽")                  # emoji fallback badge
    color = db.Column(db.String(7), default="#4361EE")             # accent color for the league

    teams = db.relationship("Team", backref="league", lazy=True, cascade="all, delete-orphan")
    matches = db.relationship("Match", backref="league", lazy=True, cascade="all, delete-orphan")

    def standings(self):
        return (Standing.query.filter_by(league_id=self.id)
                .order_by(Standing.position.asc()).all())


class Team(db.Model):
    __tablename__ = "teams"

    id = db.Column(db.Integer, primary_key=True)
    league_id = db.Column(db.Integer, db.ForeignKey("leagues.id"), nullable=False)
    name = db.Column(db.String(80), nullable=False)
    short_name = db.Column(db.String(10), nullable=False)
    crest_initials = db.Column(db.String(4), default="")
    primary_color = db.Column(db.String(7), default="#4361EE")
    founded = db.Column(db.Integer, default=1900)
    venue = db.Column(db.String(100), default="")

    players = db.relationship("Player", backref="team", lazy=True, cascade="all, delete-orphan")

    def standing(self):
        return Standing.query.filter_by(team_id=self.id).first()


class Standing(db.Model):
    __tablename__ = "standings"

    id = db.Column(db.Integer, primary_key=True)
    league_id = db.Column(db.Integer, db.ForeignKey("leagues.id"), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey("teams.id"), nullable=False)
    position = db.Column(db.Integer, nullable=False)
    played = db.Column(db.Integer, default=0)
    won = db.Column(db.Integer, default=0)
    drawn = db.Column(db.Integer, default=0)
    lost = db.Column(db.Integer, default=0)
    goals_for = db.Column(db.Integer, default=0)
    goals_against = db.Column(db.Integer, default=0)
    points = db.Column(db.Integer, default=0)
    form = db.Column(db.String(10), default="")   # e.g. "WWDLW" (most recent last)

    team = db.relationship("Team", lazy=True)

    @property
    def goal_diff(self):
        return self.goals_for - self.goals_against


class Player(db.Model):
    __tablename__ = "players"

    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey("teams.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(4), nullable=False)   # GK / DF / MF / FW
    shirt_number = db.Column(db.Integer, default=0)
    nationality = db.Column(db.String(60), default="")
    age = db.Column(db.Integer, default=25)
    appearances = db.Column(db.Integer, default=0)
    goals = db.Column(db.Integer, default=0)
    assists = db.Column(db.Integer, default=0)
    yellow_cards = db.Column(db.Integer, default=0)
    red_cards = db.Column(db.Integer, default=0)
    minutes = db.Column(db.Integer, default=0)
    avg_rating = db.Column(db.Float, default=6.8)
    market_value_eur = db.Column(db.Integer, default=0)

    def rating_tier(self):
        if self.avg_rating >= 7.5:
            return "elite"
        elif self.avg_rating >= 6.8:
            return "good"
        elif self.avg_rating >= 6.0:
            return "average"
        return "poor"


class Match(db.Model):
    __tablename__ = "matches"

    id = db.Column(db.Integer, primary_key=True)
    league_id = db.Column(db.Integer, db.ForeignKey("leagues.id"), nullable=False)
    home_team_id = db.Column(db.Integer, db.ForeignKey("teams.id"), nullable=False)
    away_team_id = db.Column(db.Integer, db.ForeignKey("teams.id"), nullable=False)
    home_score = db.Column(db.Integer, default=0)
    away_score = db.Column(db.Integer, default=0)
    status = db.Column(db.String(12), default="FT")   # LIVE / FT / NS
    minute = db.Column(db.Integer, default=90)
    matchday = db.Column(db.Integer, default=1)
    kickoff = db.Column(db.DateTime, default=datetime.utcnow)
    home_formation = db.Column(db.String(10), default="4-3-3")
    away_formation = db.Column(db.String(10), default="4-3-3")
    venue = db.Column(db.String(100), default="")

    home_team = db.relationship("Team", foreign_keys=[home_team_id])
    away_team = db.relationship("Team", foreign_keys=[away_team_id])
    lineups = db.relationship("LineupEntry", backref="match", lazy=True, cascade="all, delete-orphan")

    def top_performers(self, limit=3):
        return (LineupEntry.query.filter_by(match_id=self.id)
                .order_by(LineupEntry.rating.desc()).limit(limit).all())


class LineupEntry(db.Model):
    """One row per player appearing in a given match (starter or sub)."""
    __tablename__ = "lineup_entries"

    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey("matches.id"), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey("teams.id"), nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey("players.id"), nullable=False)
    is_starting = db.Column(db.Boolean, default=True)
    pos_x = db.Column(db.Float, default=50)   # 0-100 pitch coordinate
    pos_y = db.Column(db.Float, default=50)
    position_label = db.Column(db.String(4), default="MF")
    rating = db.Column(db.Float, default=6.8)
    goals = db.Column(db.Integer, default=0)
    assists = db.Column(db.Integer, default=0)
    yellow_card = db.Column(db.Boolean, default=False)
    red_card = db.Column(db.Boolean, default=False)
    subbed_off_minute = db.Column(db.Integer, nullable=True)

    player = db.relationship("Player", lazy=True)
    team = db.relationship("Team", lazy=True)
