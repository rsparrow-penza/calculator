// Calculator.jsx — визуальная часть калькулятора: дисплей и кнопки.
//
// Это «глупый» компонент (presentational component): сам он ничего не считает,
// а лишь рисует то, что получил в props, и сообщает родителю о кликах.
// Вся логика и состояние живут в App.jsx.

import { useEffect } from 'react'

// Описание кнопок: value — что добавить в выражение, label — что показать.
const KEYS = [
  ['7', '7'], ['8', '8'], ['9', '9'], ['÷', '/'],
  ['4', '4'], ['5', '5'], ['6', '6'], ['×', '*'],
  ['1', '1'], ['2', '2'], ['3', '3'], ['−', '-'],
  ['0', '0'], ['.', '.'], ['(', '('], ['+', '+'],
]

export default function Calculator({
  expression,   // набранное выражение, например "7+2*3"
  result,       // последний результат или null
  error,        // текст ошибки или ''
  loading,      // идёт ли запрос к серверу
  onInput,      // колбэки, объявленные в App.jsx
  onEquals,
  onClear,
  onBackspace,
}) {
  // Вешаем слушатель на всё окно. Функция-обработчик объявлена внутри эффекта,
  // чтобы не «застыть» в замыкании со старыми пропсами; при каждой смене
  // колбэков слушатель пересоздаётся, а при размонтировании — убирается.
  useEffect(() => {
    function handleKeyDown(e) {
      if ('0123456789+-*/().'.includes(e.key)) onInput(e.key)
      else if (e.key === 'Enter' || e.key === '=') onEquals()
      else if (e.key === 'Backspace') onBackspace()
      else if (e.key === 'Escape') onClear()
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [onInput, onEquals, onBackspace, onClear])

  return (
    <section className="calculator" aria-label="Калькулятор">
      {/* Дисплей: показывает выражение и результат */}
      <div className="display">
        <div className="display-expression">{expression || '\u00A0'}</div>
        {error
          ? <div className="display-error">{error}</div>
          : <div className="display-result">{result ?? '\u00A0'}</div>}
      </div>

      {/* Ряд служебных кнопок над цифровой сеткой */}
      <div className="controls">
        <button className="key key-clear" onClick={onClear}>C</button>
        <button className="key key-back" onClick={onBackspace}>⌫</button>
        <button className="key key-equals" onClick={onEquals} disabled={loading || !expression}>
          {loading ? '…' : '='}
        </button>
      </div>

      {/* Цифры и операции: сетка 4×4 */}
      <div className="keys">
        {KEYS.map(([label, value]) => (
          <button key={label} className="key" onClick={() => onInput(value)}>
            {label}
          </button>
        ))}
      </div>
    </section>
  )
}
