// Calculator.jsx — визуальная часть калькулятора: дисплей и кнопки.
//
// Это «глупый» компонент (presentational component): сам он ничего не считает,
// а лишь рисует то, что получил в props, и сообщает родителю о кликах.
// Вся логика и состояние живут в App.jsx.

import { useEffect } from 'react'

// Один массив описывает всю сетку 6×4. Поля:
//   label   — что написано на кнопке
//   value   — что добавить в выражение при клике (для обычных кнопок)
//   kind    — служебные кнопки (очистка, стереть, равно) — без value
const KEYS = [
  { label: 'C', kind: 'clear' },  { label: '⌫', kind: 'back' },
  { label: '(', value: '(' },     { label: ')', value: ')' },

  { label: '7', value: '7' },     { label: '8', value: '8' },
  { label: '9', value: '9' },     { label: '÷', value: '/' },

  { label: '4', value: '4' },     { label: '5', value: '5' },
  { label: '6', value: '6' },     { label: '×', value: '*' },

  { label: '1', value: '1' },     { label: '2', value: '2' },
  { label: '3', value: '3' },     { label: '−', value: '-' },

  { label: '0', value: '0' },     { label: '.', value: '.' },
  { label: '+', value: '+' },     { label: '=', kind: 'equals' },

  { label: 'π', value: 'pi' },    { label: 'sin', value: 'sin(' },
  { label: 'cos', value: 'cos(' },{ label: 'tan', value: 'tan(' },

  { label: '√', value: 'sqrt(' }, { label: '∛', value: 'cbrt(' },
  { label: 'ln', value: 'ln(' },  { label: 'log', value: 'log(' },
]

export default function Calculator({
  expression,   // набранное выражение, например "(1+2)*3"
  result,       // последний результат или null
  error,        // текст ошибки или ''
  loading,      // идёт ли запрос к серверу
  onInput,      // колбэки, объявленные в App.jsx
  onEquals,
  onClear,
  onBackspace,
}) {
  // Вешаем слушатель клавиатуры на всё окно. Функция-обработчик объявлена
  // внутри эффекта, чтобы не «застыть» в замыкании со старыми пропсами;
  // при смене колбэков слушатель пересоздаётся, при размонтировании — убирается.
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
        <div className="display-expression">{pretty(expression) || '\u00A0'}</div>
        {error
          ? <div className="display-error">{error}</div>
          : <div className="display-result">{result ?? '\u00A0'}</div>}
      </div>

      {/* Сетка кнопок */}
      <div className="keys">
        {KEYS.map(({ label, value, kind }) => {
          if (kind === 'clear')
            return <button key={label} className="key key-clear" onClick={onClear}>{label}</button>
          if (kind === 'back')
            return <button key={label} className="key key-back" onClick={onBackspace}>{label}</button>
          if (kind === 'equals')
            return (
              <button key={label} className="key key-equals" onClick={onEquals} disabled={loading || !expression}>
                {loading ? '…' : label}
              </button>
            )
          // Обычная кнопка: цифра, оператор, скобка или функция
          return (
            <button
              key={label}
              className={`key${value?.endsWith('(') && value !== '(' ? ' key-func' : ''}`}
              onClick={() => onInput(value)}
            >
              {label}
            </button>
          )
        })}
      </div>
    </section>
  )
}

// Внутренний вид (* / pi sqrt( …) показываем человеку привычно (× ÷ π  …)
function pretty(expression) {
  return expression
    .replace(/\*/g, '×')
    .replace(/\//g, '÷')
    .replace(/\bpi\b/g, 'π')
    .replace(/sqrt\(/g, '√(')
    .replace(/cbrt\(/g, '∛(')
}
