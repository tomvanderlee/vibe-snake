# Minesweeper

This project is entirely vibe coded by Claude (https://claude.ai) as an experiment in AI-driven development. No human wrote any of the source code.

A classic Minesweeper game with a Python/FastAPI backend and a React frontend.

## Stack

- Backend: Python, FastAPI, SQLModel, SQLite, Alembic
- Frontend: React 18, Vite
- Package managers: uv (Python), yarn (Node)

## Running locally

Prerequisites:
- uv: https://docs.astral.sh/uv/getting-started/installation/
- yarn: https://yarnpkg.com/getting-started/install

Backend:
```
cd backend
uv sync
uv run alembic upgrade head
uv run uvicorn app:app --reload --port 5000
```

Frontend:
```
cd frontend
yarn install
yarn dev
```

Open http://127.0.0.1:3000 in your browser.

## Database migrations

The game state is persisted in `backend/minesweeper.db` (SQLite). Alembic manages the schema.

```
cd backend
uv run alembic revision --autogenerate -m "describe your change"
uv run alembic upgrade head
```

## Gameplay

| Action | Control |
|--------|---------|
| Reveal cell | Left click |
| Flag / unflag | Right click |
| Chord (reveal neighbours) | Double click a number |

Choose a difficulty from the dropdown: Beginner (9x9, 10 mines), Intermediate (16x16, 40 mines), or Expert (16x30, 99 mines), then click **New Game**.
