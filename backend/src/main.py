from fastapi import FastAPI, Depends, HTTPException, WebSocket, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from models import User, Game, Bet, Base
from database import SessionLocal, engine
from pydantic import BaseModel
import asyncio
import random

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



# Background task to update scores
async def update_game_scores():
    db = SessionLocal()
    try:
        while True:
            games = db.query(Game).filter(Game.status == "in progress").all()
            for game in games:
                # Randomly increment scores
                score_team_1_increment = random.choice([3, 7])
                score_team_2_increment = random.choice([3, 7])
                game.score_team_1 += score_team_1_increment
                game.score_team_2 += score_team_2_increment

                # Debugging output to check if scores are updating
                print(f"Updating game {game.id}: Team 1 score += {score_team_1_increment}, Team 2 score += {score_team_2_increment}")
                print(f"New scores - Team 1: {game.score_team_1}, Team 2: {game.score_team_2}")

                # Check if the game should end
                if game.score_team_1 >= 20 or game.score_team_2 >= 20:  # End threshold
                    game.status = "finished"
                    game.result = "team_1" if game.score_team_1 > game.score_team_2 else "team_2"
                    print(f"Game {game.id} finished! Result: {game.result}")
                    
                
                # Commit updates to the database
                db.commit()
            await asyncio.sleep(5)  # Update scores every 5 seconds
    finally:
        db.close()


@app.on_event("startup")
async def startup_event():
    # Start background task on server startup
    asyncio.create_task(update_game_scores())
    

# WebSocket connection for live updates
@app.websocket("/game/{game_id}/ws")
async def websocket_endpoint(websocket: WebSocket, game_id: int):
    await websocket.accept()
    db = SessionLocal()
    try:
        while True:
            game = db.query(Game).filter(Game.id == game_id).first()
            if game:
                # Send game update to client
                message = {
                    "team_1": game.team_1,
                    "team_2": game.team_2,
                    "score_team_1": game.score_team_1,
                    "score_team_2": game.score_team_2,
                    "status": game.status,
                    "result": game.result,
                }
                await websocket.send_json(message)
                
                # Close WebSocket if game is finished
                if game.status == "finished":
                    break
                
            await asyncio.sleep(5)  # Send updates every 5 seconds
    finally:
        db.close()
