from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Literal

from game import GameState, GameStatus, MinesweeperGame

app = FastAPI(title="Minesweeper API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

games: dict[str, MinesweeperGame] = {}

DIFFICULTIES: dict[str, dict[str, int]] = {
    "beginner": {"rows": 9, "cols": 9, "mines": 10},
    "intermediate": {"rows": 16, "cols": 16, "mines": 40},
    "expert": {"rows": 16, "cols": 30, "mines": 99},
}


class NewGameRequest(BaseModel):
    difficulty: Literal["beginner", "intermediate", "expert", "custom"] = "beginner"
    rows: int = Field(default=9, ge=5, le=30)
    cols: int = Field(default=9, ge=5, le=50)
    mines: int = Field(default=10, ge=1)


class CellRequest(BaseModel):
    row: int = Field(ge=0)
    col: int = Field(ge=0)


def get_game(game_id: str) -> MinesweeperGame:
    game = games.get(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game


@app.post("/api/game", response_model=GameState)
def new_game(body: NewGameRequest) -> GameState:
    if body.difficulty == "custom":
        max_mines = body.rows * body.cols - 9
        config = {
            "rows": body.rows,
            "cols": body.cols,
            "mines": min(body.mines, max_mines),
        }
    else:
        config = DIFFICULTIES[body.difficulty]

    game = MinesweeperGame(**config)
    games[game.id] = game
    return game.to_state()


@app.get("/api/game/{game_id}", response_model=GameState)
def get_game_state(game_id: str) -> GameState:
    return get_game(game_id).to_state()


@app.post("/api/game/{game_id}/reveal", response_model=GameState)
def reveal_cell(game_id: str, body: CellRequest) -> GameState:
    game = get_game(game_id)
    if body.row >= game.rows or body.col >= game.cols:
        raise HTTPException(status_code=422, detail="Cell out of bounds")
    return game.reveal(body.row, body.col).to_state()


@app.post("/api/game/{game_id}/flag", response_model=GameState)
def flag_cell(game_id: str, body: CellRequest) -> GameState:
    game = get_game(game_id)
    if body.row >= game.rows or body.col >= game.cols:
        raise HTTPException(status_code=422, detail="Cell out of bounds")
    return game.flag(body.row, body.col).to_state()


@app.post("/api/game/{game_id}/chord", response_model=GameState)
def chord_cell(game_id: str, body: CellRequest) -> GameState:
    game = get_game(game_id)
    if body.row >= game.rows or body.col >= game.cols:
        raise HTTPException(status_code=422, detail="Cell out of bounds")
    return game.chord(body.row, body.col).to_state()
