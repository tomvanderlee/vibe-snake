from typing import Annotated, Literal

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlmodel import Session

from database import get_session
from game import GameRecord, GameState, MinesweeperGame


app = FastAPI(title="Minesweeper API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DIFFICULTIES: dict[str, dict[str, int]] = {
    "beginner": {"rows": 9, "cols": 9, "mines": 10},
    "intermediate": {"rows": 16, "cols": 16, "mines": 40},
    "expert": {"rows": 16, "cols": 30, "mines": 99},
}

SessionDep = Annotated[Session, Depends(get_session)]


class NewGameRequest(BaseModel):
    difficulty: Literal["beginner", "intermediate", "expert", "custom"] = "beginner"
    rows: int = Field(default=9, ge=5, le=30)
    cols: int = Field(default=9, ge=5, le=50)
    mines: int = Field(default=10, ge=1)


class CellRequest(BaseModel):
    row: int = Field(ge=0)
    col: int = Field(ge=0)


def load_game(game_id: str, session: Session) -> MinesweeperGame:
    record = session.get(GameRecord, game_id)
    if not record:
        raise HTTPException(status_code=404, detail="Game not found")
    return MinesweeperGame.from_record(record)


def save_game(game: MinesweeperGame, session: Session) -> GameState:
    record = game.to_record()
    session.merge(record)
    session.commit()
    return game.to_state()


@app.post("/api/game", response_model=GameState)
def new_game(body: NewGameRequest, session: SessionDep) -> GameState:
    if body.difficulty == "custom":
        max_mines = body.rows * body.cols - 9
        config = {"rows": body.rows, "cols": body.cols, "mines": min(body.mines, max_mines)}
    else:
        config = DIFFICULTIES[body.difficulty]

    game = MinesweeperGame(**config)
    return save_game(game, session)


@app.get("/api/game/{game_id}", response_model=GameState)
def get_game(game_id: str, session: SessionDep) -> GameState:
    return load_game(game_id, session).to_state()


@app.post("/api/game/{game_id}/reveal", response_model=GameState)
def reveal_cell(game_id: str, body: CellRequest, session: SessionDep) -> GameState:
    game = load_game(game_id, session)
    if body.row >= game.rows or body.col >= game.cols:
        raise HTTPException(status_code=422, detail="Cell out of bounds")
    game.reveal(body.row, body.col)
    return save_game(game, session)


@app.post("/api/game/{game_id}/flag", response_model=GameState)
def flag_cell(game_id: str, body: CellRequest, session: SessionDep) -> GameState:
    game = load_game(game_id, session)
    if body.row >= game.rows or body.col >= game.cols:
        raise HTTPException(status_code=422, detail="Cell out of bounds")
    game.flag(body.row, body.col)
    return save_game(game, session)


@app.post("/api/game/{game_id}/chord", response_model=GameState)
def chord_cell(game_id: str, body: CellRequest, session: SessionDep) -> GameState:
    game = load_game(game_id, session)
    if body.row >= game.rows or body.col >= game.cols:
        raise HTTPException(status_code=422, detail="Cell out of bounds")
    game.chord(body.row, body.col)
    return save_game(game, session)
