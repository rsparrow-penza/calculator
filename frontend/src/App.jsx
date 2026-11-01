// App.jsx — корневой компонент нашего приложения.
//
// Он хранит «общее состояние»: текущее выражение, результат, историю и ошибку.
// Состояние живёт здесь, потому что им пользуются и калькулятор, и история.
// React сам перерисует интерфейс, когда состояние изменится через setResult(...).

import { useCallback, useEffect, useState } from 'react'
import Calculator from './Calculator.jsx'
import History from './History.jsx'
import './App.css'

export default function App() {
  // Хуки useState создают «ячейки» состояния
  const [expression, setExpression] = useState('')     // то, что набрал пользователь: "7+2*3"
  const [result, setResult] = useState(null)          // последний результат: "13"
  const [error, setError] = useState('')              // текст ошибки, если сервер её вернул
  const [history, setHistory] = useState([])          // список вычислений из базы
  const [loading, setLoading] = useState(false)       // идёт ли сейчас запрос к серверу

  // Загружаем историю вычислений с бэкенда (GET /api/history).
  // useCallback — чтобы функцию можно было вызывать и из эффектов, и после вычислений.
  const loadHistory = useCallback(async () => {
    try {
      const res = await fetch('/api/history')
      const data = await res.json()
      setHistory(data)
    } catch {
      // Сервер может быть ещё не запущен — не роняем интерфейс
      console.warn('Не удалось загрузить историю: заведите бэкенд (python3 app.py)')
    }
  }, [])

  // useEffect с пустым массивом зависимостей выполняется один раз — при открытии
  useEffect(() => {
    loadHistory()
  }, [loadHistory])

  // Главный действие: нажать «=». Просим сервер посчитать и сохранить.
  async function handleEquals() {
    if (!expression || loading) return
    setLoading(true)
    setError('')
    try {
      const res = await fetch('/api/calculate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ expression }),
      })
      const data = await res.json()

      if (!res.ok) {
        // Сервер вернул ошибку ("Деление на ноль" и т. п.)
        setError(data.error || 'Ошибка вычисления')
      } else {
        // Python отдаёт деление как float ("3.0") — прибираем хвостовые нули
        const n = Number(data.result)
        setResult(Number.isInteger(n) ? String(n) : data.result)
        setHistory(await (await fetch('/api/history')).json()) // обновляем историю
      }
    } catch {
      setError('Сервер недоступен. Запустите бэкенд: python3 app.py')
    } finally {
      setLoading(false)
    }
  }

  // Очистить поле (кнопка C)
  function handleClear() {
    setExpression('')
    setResult(null)
    setError('')
  }

  // Удалить последний символ (⌫)
  function handleBackspace() {
    setExpression((prev) => prev.slice(0, -1))
  }

  // Добавить цифру или оператор (кнопки 0-9, +, -, …)
  function handleInput(value) {
    setResult(null) // новый ввод — старый результат больше не актуален
    setExpression((prev) => prev + value)
  }

  // Полная очистка истории (кнопка «Очистить историю»)
  async function handleClearHistory() {
    await fetch('/api/history', { method: 'DELETE' })
    loadHistory()
  }

  return (
    <div className="app">
      <h1>Калькулятор</h1>

      <div className="layout">
        <Calculator
          expression={expression}
          result={result}
          error={error}
          loading={loading}
          onInput={handleInput}
          onEquals={handleEquals}
          onClear={handleClear}
          onBackspace={handleBackspace}
        />

        <History items={history} onClear={handleClearHistory} />
      </div>
    </div>
  )
}
