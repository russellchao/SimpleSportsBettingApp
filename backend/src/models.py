from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)  # Remember to hash passwords in production
    points = Column(Float, default=100.0)  # Starting points

class Game(Base):
    __tablename__ = "games"
    
    id = Column(Integer, primary_key=True, index=True)
    team_1 = Column(String)
    team_2 = Column(String)
    start_time = Column(DateTime, default=datetime.utcnow)
    result = Column(String, nullable=True)  # "team_1", "team_2", or None if undecided

class Bet(Base):
    __tablename__ = "bets"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    game_id = Column(Integer, ForeignKey("games.id"))
    team = Column(String)  # Either "team_1" or "team_2"
    points = Column(Float)
    placed_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="bets")
    game = relationship("Game", back_populates="bets")

User.bets = relationship("Bet", back_populates="user")
Game.bets = relationship("Bet", back_populates="game")
