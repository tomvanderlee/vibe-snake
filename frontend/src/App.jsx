import { useState, useEffect, useCallback, useRef } from 'react'

const API = '/api'

const DIFFICULTIES = ['beginner', 'intermediate', 'expert']

const NUMBER_CLASSES = ['', 'n1', 'n2', 'n3', 'n4', 'n5', 'n6', 'n7', 'n8']

function Cell({ cell, row, col, onReveal, onFlag, onChord, gameStatus }) {
  const handleClick = (e) => {
    e.preventDefault()
    if (gameStatus !== 'playing') return
    if (cell.flagged || cell.revealed) {
      if (cell.revealed && cell.adjacent > 0) onChord(row, col)
      return
    }
    onReveal(row, col)
  }

  const handleRightClick = (e) => {
    e.preventDefault()
    if (gameStatus !== 'playing') return
    if (!cell.revealed) onFlag(row, col)
  }

  const handleDoubleClick = (e) => {
    e.preventDefault()
    if (gameStatus !== 'playing') return
    if (cell.revealed && cell.adjacent > 0) onChord(row, col)
  }

  let className = 'cell'
  let content = ''

  if (cell.revealed) {
    if (cell.mine) {
      className += ' mine-hit'
      content = '💣'
    } else {
      className += ' revealed'
      if (cell.adjacent > 0) {
        className += ` ${NUMBER_CLASSES[cell.adjacent]}`
        content = cell.adjacent
      }
    }
  } else if (cell.flagged) {
    className += ' flagged'
    content = '🚩'
  } else if (cell.mine && gameStatus === 'lost') {
    className += ' mine-revealed'
    content = '💣'
  } else {
    className += ' hidden'
  }

  return (
    <div
      className={className}
      onClick={handleClick}
      onContextMenu={handleRightClick}
      onDoubleClick={handleDoubleClick}
    >
      {content}
    </div>
  )
}

function Board({ game, onReveal, onFlag, onChord }) {
  if (!game) return null
  return (
    <div className="board-wrapper">
      <div className="board">
        {game.board.map((row, r) => (
          <div key={r} className="board-row">
            {row.map((cell, c) => (
              <Cell
                key={c}
                cell={cell}
                row={r}
                col={c}
                onReveal={onReveal}
                onFlag={onFlag}
                onChord={onChord}
                gameStatus={game.status}
              />
            ))}
          </div>
        ))}
      </div>
    </div>
  )
}

export default function App() {
  const [game, setGame] = useState(null)
  const [difficulty, setDifficulty] = useState('beginner')
  const [loading, setLoading] = useState(false)
  const [elapsed, setElapsed] = useState(0)
  const timerRef = useRef(null)
  const startTimeRef = useRef(null)
  const gameStartedRef = useRef(false)

  const startTimer = useCallback(() => {
    if (timerRef.current) clearInterval(timerRef.current)
    startTimeRef.current = Date.now() - elapsed * 1000
    timerRef.current = setInterval(() => {
      setElapsed(Math.floor((Date.now() - startTimeRef.current) / 1000))
    }, 1000)
  }, [elapsed])

  const stopTimer = useCallback(() => {
    if (timerRef.current) clearInterval(timerRef.current)
    timerRef.current = null
  }, [])

  const newGame = useCallback(async () => {
    setLoading(true)
    stopTimer()
    setElapsed(0)
    gameStartedRef.current = false
    try {
      const res = await fetch(`${API}/game`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ difficulty }),
      })
      const data = await res.json()
      setGame(data)
    } finally {
      setLoading(false)
    }
  }, [difficulty, stopTimer])

  useEffect(() => {
    newGame()
    return () => stopTimer()
  }, [])  // eslint-disable-line

  const handleGameUpdate = useCallback((data) => {
    setGame(data)
    if (!gameStartedRef.current && data.status === 'playing') {
      gameStartedRef.current = true
      startTimer()
    }
    if (data.status !== 'playing') {
      stopTimer()
    }
  }, [startTimer, stopTimer])

  const onReveal = useCallback(async (row, col) => {
    if (!game) return
    const res = await fetch(`${API}/game/${game.id}/reveal`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ row, col }),
    })
    handleGameUpdate(await res.json())
  }, [game, handleGameUpdate])

  const onFlag = useCallback(async (row, col) => {
    if (!game) return
    const res = await fetch(`${API}/game/${game.id}/flag`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ row, col }),
    })
    handleGameUpdate(await res.json())
  }, [game, handleGameUpdate])

  const onChord = useCallback(async (row, col) => {
    if (!game) return
    const res = await fetch(`${API}/game/${game.id}/chord`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ row, col }),
    })
    handleGameUpdate(await res.json())
  }, [game, handleGameUpdate])

  const minesRemaining = game ? game.mine_count - game.flags_used : 0
  const face = game?.status === 'won' ? '😎' : game?.status === 'lost' ? '😵' : '🙂'

  return (
    <div className="app">
      <h1>MINESWEEPER</h1>

      <div className="controls">
        <select value={difficulty} onChange={e => setDifficulty(e.target.value)}>
          {DIFFICULTIES.map(d => (
            <option key={d} value={d}>{d.charAt(0).toUpperCase() + d.slice(1)}</option>
          ))}
        </select>
        <button className="btn-new-game" onClick={newGame} disabled={loading}>
          New Game
        </button>
      </div>

      <div className="status-bar">
        <span className="mines">💣 {minesRemaining}</span>
        <span className="face" onClick={newGame} title="New Game">{face}</span>
        <span className="timer">⏱ {String(elapsed).padStart(3, '0')}</span>
      </div>

      {game?.status !== 'playing' && game && (
        <div className={`game-over-banner ${game.status}`}>
          {game.status === 'won' ? '🎉 YOU WIN!' : '💥 GAME OVER'}
        </div>
      )}

      {loading ? (
        <div className="loading">Loading...</div>
      ) : (
        <Board game={game} onReveal={onReveal} onFlag={onFlag} onChord={onChord} />
      )}
    </div>
  )
}
