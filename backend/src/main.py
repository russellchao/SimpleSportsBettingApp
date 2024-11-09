# main.py
from fastapi import FastAPI, Depends, HTTPException, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from models import User, Game, Bet, Base
from database import SessionLocal, engine
from pydantic import BaseModel
import asyncio

# Initialize the database
Base.metadata.create_all(bind=engine)

# Initialize the FastAPI app
app = FastAPI()

# Allow CORS for React frontend
app.add_middleware(CORSMiddleware, 
                   allow_origins=["*"], 
                   allow_credentials=True, 
                   allow_methods=["*"], 
                   allow_headers=["*"])


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Pydantic schemas
class UserCreate(BaseModel):
    username: str
    password: str

class GameCreate(BaseModel):
    team_1: str
    team_2: str

class BetCreate(BaseModel):
    user_id: int
    game_id: int
    team: str
    points: float



# Endpoints

# Endpoint to create a user
@app.post("/users/")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    new_user = User(username=user.username, password=user.password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user



# Endpoint to create a game
@app.post("/games/")
def create_game(game: GameCreate, db: Session = Depends(get_db)):
    new_game = Game(team_1=game.team_1, team_2=game.team_2)
    db.add(new_game)
    db.commit()
    db.refresh(new_game)
    return new_game



# Endpoint to place a bet
@app.post("/bets/")
def place_bet(bet: BetCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == bet.user_id).first()
    game = db.query(Game).filter(Game.id == bet.game_id).first()
    if not user or not game:
        raise HTTPException(status_code=404, detail="User or Game not found")
    
    if user.points < bet.points:
        raise HTTPException(status_code=400, detail="Insufficient points")
    
    new_bet = Bet(user_id=bet.user_id, game_id=bet.game_id, team=bet.team, points=bet.points)
    user.points -= bet.points  # Deduct points
    db.add(new_bet)
    db.commit()
    db.refresh(new_bet)
    return new_bet



# WebSocket connection for live updates
@app.websocket("/ws/game/{game_id}")
async def websocket_endpoint(websocket: WebSocket, game_id: int):
    await websocket.accept()
    while True:
        # In real scenario, you'd update based on actual game data
        # Here, we’ll simulate updates
        await asyncio.sleep(5)  # Wait for 5 seconds
        await websocket.send_text(f"Game {game_id} updated score")  # Example update
