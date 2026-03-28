import random
import uuid
from enum import Enum
from pydantic import BaseModel, Field


class GameStatus(str, Enum):
    playing = "playing"
    won = "won"
    lost = "lost"


class CellState(BaseModel):
    revealed: bool
    flagged: bool
    mine: bool
    adjacent: int


class GameState(BaseModel):
    id: str
    rows: int
    cols: int
    mine_count: int
    flags_used: int
    status: GameStatus
    board: list[list[CellState]]


class Cell:
    def __init__(self):
        self.mine = False
        self.revealed = False
        self.flagged = False
        self.adjacent = 0


class MinesweeperGame:
    def __init__(self, rows: int = 9, cols: int = 9, mines: int = 10):
        self.id = str(uuid.uuid4())
        self.rows = rows
        self.cols = cols
        self.mine_count = mines
        self.status = GameStatus.playing
        self.board: list[list[Cell]] = [[Cell() for _ in range(cols)] for _ in range(rows)]
        self.revealed_count = 0
        self.first_move = True
        self.flags_used = 0

    def _place_mines(self, safe_row: int, safe_col: int) -> None:
        safe_cells = set()
        for dr in range(-1, 2):
            for dc in range(-1, 2):
                r, c = safe_row + dr, safe_col + dc
                if 0 <= r < self.rows and 0 <= c < self.cols:
                    safe_cells.add((r, c))

        all_cells = [
            (r, c)
            for r in range(self.rows)
            for c in range(self.cols)
            if (r, c) not in safe_cells
        ]
        mine_cells = random.sample(all_cells, min(self.mine_count, len(all_cells)))

        for r, c in mine_cells:
            self.board[r][c].mine = True

        for r in range(self.rows):
            for c in range(self.cols):
                if not self.board[r][c].mine:
                    count = sum(
                        1
                        for dr in range(-1, 2)
                        for dc in range(-1, 2)
                        if 0 <= r + dr < self.rows
                        and 0 <= c + dc < self.cols
                        and self.board[r + dr][c + dc].mine
                    )
                    self.board[r][c].adjacent = count

    def reveal(self, row: int, col: int) -> "MinesweeperGame":
        if self.status != GameStatus.playing:
            return self

        cell = self.board[row][col]
        if cell.revealed or cell.flagged:
            return self

        if self.first_move:
            self._place_mines(row, col)
            self.first_move = False

        self._reveal_cell(row, col)
        self._check_win()
        return self

    def _reveal_cell(self, row: int, col: int) -> None:
        cell = self.board[row][col]
        if cell.revealed or cell.flagged:
            return

        cell.revealed = True
        self.revealed_count += 1

        if cell.mine:
            self.status = GameStatus.lost
            for r in range(self.rows):
                for c in range(self.cols):
                    if self.board[r][c].mine:
                        self.board[r][c].revealed = True
            return

        if cell.adjacent == 0:
            for dr in range(-1, 2):
                for dc in range(-1, 2):
                    nr, nc = row + dr, col + dc
                    if 0 <= nr < self.rows and 0 <= nc < self.cols:
                        self._reveal_cell(nr, nc)

    def flag(self, row: int, col: int) -> "MinesweeperGame":
        if self.status != GameStatus.playing:
            return self

        cell = self.board[row][col]
        if cell.revealed:
            return self

        if cell.flagged:
            cell.flagged = False
            self.flags_used -= 1
        else:
            cell.flagged = True
            self.flags_used += 1

        return self

    def chord(self, row: int, col: int) -> "MinesweeperGame":
        if self.status != GameStatus.playing:
            return self

        cell = self.board[row][col]
        if not cell.revealed or cell.adjacent == 0:
            return self

        flagged_neighbors = 0
        unrevealed_neighbors: list[tuple[int, int]] = []
        for dr in range(-1, 2):
            for dc in range(-1, 2):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = row + dr, col + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    n = self.board[nr][nc]
                    if n.flagged:
                        flagged_neighbors += 1
                    elif not n.revealed:
                        unrevealed_neighbors.append((nr, nc))

        if flagged_neighbors == cell.adjacent:
            for nr, nc in unrevealed_neighbors:
                self._reveal_cell(nr, nc)
            self._check_win()

        return self

    def _check_win(self) -> None:
        if self.status == GameStatus.lost:
            return
        safe_cells = self.rows * self.cols - self.mine_count
        if self.revealed_count >= safe_cells:
            self.status = GameStatus.won
            for r in range(self.rows):
                for c in range(self.cols):
                    if self.board[r][c].mine and not self.board[r][c].flagged:
                        self.board[r][c].flagged = True

    def to_state(self) -> GameState:
        board_data = [
            [
                CellState(
                    revealed=cell.revealed,
                    flagged=cell.flagged,
                    mine=cell.mine if (cell.revealed or self.status != GameStatus.playing) else False,
                    adjacent=cell.adjacent if cell.revealed else 0,
                )
                for cell in row
            ]
            for row in self.board
        ]
        return GameState(
            id=self.id,
            rows=self.rows,
            cols=self.cols,
            mine_count=self.mine_count,
            flags_used=self.flags_used,
            status=self.status,
            board=board_data,
        )
