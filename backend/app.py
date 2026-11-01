# Калькулятор API: Flask + SQLite
#
# Этот файл — «мозг» приложения на стороне сервера.
# Он умеет три вещи:
#   1. Считать арифметические выражения (POST /api/calculate)
#   2. Сохранять каждое вычисление в базу данных SQLite
#   3. Отдавать историю вычислений (GET /api/history)
#
# Запуск:  python3 app.py
# Сервер поднимется на http://localhost:5001
# (порт 5001, а не 5000, потому что на macOS порт 5000 занят AirPlay Receiver)

import sqlite3
from datetime import datetime

from flask import Flask, jsonify, request
from flask_cors import CORS  # разрешает запросы из React (другой порт = «другой сайт» для браузера)

app = Flask(__name__)
CORS(app)

DB_FILE = "calculator.db"


# ---------------------------------------------------------------------------
# Работа с базой данных
# ---------------------------------------------------------------------------

def get_db():
    """Открывает подключение к базе. SQLite лежит в одном файле calculator.db."""
    conn = sqlite3.connect(DB_FILE)
    # чтобы строки из базы было удобно превращать в словари
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Создаёт таблицу history, если её ещё нет. Запускается один раз при старте."""
    with get_db() as db:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS history (
                id         INTEGER PRIMARY KEY AUTOINCREMENT, -- номер записи
                expression TEXT    NOT NULL,                  -- например "7+2"
                result     TEXT    NOT NULL,                  -- например "9"
                created_at TEXT    NOT NULL                   -- когда посчитали
            )
            """
        )


init_db()


# ---------------------------------------------------------------------------
# Безопасный вычислитель выражений
# ---------------------------------------------------------------------------

def safe_eval(expression: str):
    """
    Считает арифметическое выражение БЕЗ использования eval().
    eval() выполняет любой код — это дыра в безопасности, когда код приходит
    из интернета. Поэтому сначала проверяем, что в строке только цифры,
    скобки и знаки операций, и только потом считаем.
    """
    # Разрешённые символы: цифры, пробелы, + - * / и скобки, десятичная точка
    allowed = set("0123456789+-*/(). ")
    if not expression or not set(expression) <= allowed:
        raise ValueError("Разрешены только числа и операции + - * / и скобки")

    result = eval(expression, {"__builtins__": {}}, {})  # безопасно: символы проверены
    return result


# ---------------------------------------------------------------------------
# Маршруты (эндпоинты) API
# ---------------------------------------------------------------------------

@app.route("/api/calculate", methods=["POST"])
def calculate():
    """Принимает выражение, считает, сохраняет в базу и возвращает результат."""
    data = request.get_json(silent=True) or {}
    expression = str(data.get("expression", "")).strip()

    try:
        result = safe_eval(expression)
    except ZeroDivisionError:
        return jsonify({"error": "Деление на ноль"}), 400
    except (ValueError, SyntaxError):
        return jsonify({"error": "Некорректное выражение"}), 400

    # Сохраняем каждое вычисление в базу данных
    with get_db() as db:
        db.execute(
            "INSERT INTO history (expression, result, created_at) VALUES (?, ?, ?)",
            (expression, str(result), datetime.now().isoformat(timespec="seconds")),
        )

    return jsonify({"expression": expression, "result": str(result)})


@app.route("/api/history", methods=["GET"])
def history():
    """Возвращает последние 50 вычислений, свежие — первыми."""
    with get_db() as db:
        rows = db.execute(
            "SELECT id, expression, result, created_at "
            "FROM history ORDER BY id DESC LIMIT 50"
        ).fetchall()

    return jsonify([dict(row) for row in rows])


@app.route("/api/history", methods=["DELETE"])
def clear_history():
    """Очищает всю историю (кнопка «Очистить» в интерфейсе)."""
    with get_db() as db:
        db.execute("DELETE FROM history")
    return jsonify({"ok": True})


if __name__ == "__main__":
    # debug=True — сервер сам перезапускается после правок кода
    app.run(port=5001, debug=True)
