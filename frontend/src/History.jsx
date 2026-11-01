// History.jsx — панель истории вычислений из базы данных.
// Получает массив записей и рисует список. Каждая запись = строка в SQLite.

export default function History({ items, onClear }) {
  return (
    <aside className="history" aria-label="История вычислений">
      <div className="history-header">
        <h2>История</h2>
        {items.length > 0 && (
          <button className="history-clear" onClick={onClear}>
            Очистить
          </button>
        )}
      </div>

      {items.length === 0 ? (
        <p className="history-empty">Пока пусто — выполните первое вычисление 🙂</p>
      ) : (
        <ul className="history-list">
          {items.map((item) => (
            <li key={item.id} className="history-item">
              {/* item = { id, expression, result, created_at } — как в таблице БД */}
              <span className="history-expr">{pretty(item.expression)} =</span>
              <span className="history-result">{prettyNumber(item.result)}</span>
              <span className="history-time">{formatTime(item.created_at)}</span>
            </li>
          ))}
        </ul>
      )}
    </aside>
  )
}

// Показываем привычные значки вместо символов программирования: * → ×
function pretty(expression) {
  return expression.replace(/\*/g, '×').replace(/\//g, '÷')
}

// "2026-11-01T16:38:42" → "16:38"
function formatTime(iso) {
  const time = iso.split('T')[1]
  return time ? time.slice(0, 5) : ''
}

// Python возвращает деление как float: "3.0". Приводим к красивому виду: "3"
function prettyNumber(value) {
  const n = Number(value)
  return Number.isFinite(n) && Number.isInteger(n) ? String(n) : value
}
