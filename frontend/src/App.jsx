// App.jsx — корневой компонент нашего приложения.
//
// Он хранит «общее состояние»: текущее выражение, результат, историю и ошибку.
// Состояние живёт здесь, потому что им пользуются и калькулятор, и история.
// React сам перерисует интерфейс, когда состояние изменится через setResult(...).

import { useCallback, useEffect, useState } from 'react'
import Calculator from './Calculator.jsx'
import History from './History.jsx'
import './App.css'

// --- Вспомогательные функции «постфиксного» ввода ---

// Кнопка-функция — это значение вида "sqrt(", "sin(", "ln(" и т. п.
function isFunctionKey(value) {
  return /^[a-z]+\($/.test(value)
}

// Пытаемся применить функцию к уже набранному «последнему операнду».
// Возвращаем новое выражение или null, если накрывать нечего
// (пустая строка, выражение кончается оператором и т. д.).
function wrapPreviousOperand(expr, fn) {
  if (!expr) return null
  let start = expr.length

  if (expr.endsWith(')')) {
    // Ищем скобку, парную к последней…
    let depth = 0
    for (let i = expr.length - 1; i >= 0; i--) {
      if (expr[i] === ')') depth++
      else if (expr[i] === '(' && --depth === 0) { start = i; break }
    }
    // …и приклеиваем имя функции перед ней: sin(30) → sqrt(sin(30))
    while (start > 0 && /[a-z]/.test(expr[start - 1])) start--
  } else if (/[0-9.]/.test(expr[expr.length - 1])) {
    // Число в конце: 2.5 → sqrt(2.5). Идём назад, пока идут цифры и точка
    let i = expr.length - 1
    while (i >= 0 && /[0-9.]/.test(expr[i])) i--
    start = i + 1
  } else if (expr.endsWith('pi')) {
    start = expr.length - 2   // константа π в конце: pi → sqrt(pi)
  } else {
    return null               // конец на операторе (+, *) — накрывать нечего
  }

  const operand = expr.slice(start)
  if (!operand) return null
  return expr.slice(0, start) + fn + operand + ')'
}

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
    setExpression((prev) => {
      // «Постфиксный режим» как в мобильных калькуляторах:
      // если набрали число (или скобку/π/функцию), а потом жмём кнопку
      // функции (sqrt(, sin(, ...), то функция «накрывает» уже набранное:
      //   4 → √ → sqrt(4)          вместо бесполезного 4sqrt(
      if (isFunctionKey(value)) {
        const wrapped = wrapPreviousOperand(prev, value)
        if (wrapped !== null) return wrapped
      }
      return prev + value
    })
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
