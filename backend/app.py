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

import os
import sqlite3
from datetime import datetime

from flask import Flask, jsonify, request
from flask_cors import CORS  # разрешает запросы из React (другой порт = «другой сайт» для браузера)

app = Flask(__name__)
CORS(app)

# Путь к базе. В Docker мы пробрасываем переменную DATABASE_FILE, чтобы база
# лежала в томе (/data), который переживает пересоздание контейнера.
DB_FILE = os.environ.get("DATABASE_FILE", "calculator.db")


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
#
# Раньше здесь стояла проверка «разрешённые символы + eval()». Теперь поддерживаются
# функции (sin, cos, tan), и пропускать их через eval стало опаснее: подмена
# символа — и уже можно что-нибудь натворить.
#
# Правильный подход: разобрать строку в ДЕРЕВО операций (AST — abstract syntax
# tree, «синтаксическое дерево») и разрешить в нём только заранее известные
# узлы: числа, + - * / , скобки, π и три функции. Всё остальное — ValueError.
# Никакого eval() не становится вовсе.

import ast
import math

def _cbrt(x: float) -> float:
    """
    Кубический корень. Готовой math.cbrt нет в Python 3.9 (локальный компьютер),
    а на сервере в Docker — 3.12. Пишем сами, чтобы работало везде:
    корень нечётной степени сохраняем со знаком (∛(-8) = -2).
    """
    return math.copysign(abs(x) ** (1 / 3), x)


# Что разрешено использовать в выражении
ALLOWED_FUNCTIONS = {
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "sqrt": math.sqrt,   # квадратный корень √x
    "cbrt": _cbrt,       # кубический корень ∛x
    "ln": math.log,      # натуральный логарифм (основание e)
    "log": math.log10,   # десятичный логарифм (основание 10)
}
ALLOWED_CONSTANTS = {
    "pi": math.pi,
}


def _eval_node(node):
    """
    Рекурсивно вычисляет один узел дерева.
    Каждый elif — единственный разрешённый «кирпичик» калькулятора.
    """
    if isinstance(node, ast.Expression):          # обёртка всего выражения
        return _eval_node(node.body)

    if isinstance(node, ast.Constant):            # число: 7, 3.14
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("Разрешены только числа")

    if isinstance(node, ast.Name):                # имя: pi
        if node.id in ALLOWED_CONSTANTS:
            return ALLOWED_CONSTANTS[node.id]
        raise ValueError("Неизвестная константа")

    if isinstance(node, ast.BinOp):               # бинарная операция: a + b
        left, right = _eval_node(node.left), _eval_node(node.right)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            return left / right                   # деление на ноль поймает Flask
        raise ValueError("Неизвестная операция")

    if isinstance(node, ast.UnaryOp):             # унарный минус: -5
        value = _eval_node(node.operand)
        if isinstance(node.op, ast.USub):
            return -value
        if isinstance(node.op, ast.UAdd):
            return value
        raise ValueError("Неизвестная операция")

    if isinstance(node, ast.Call):                # вызов функции: sin(...)
        func_name = getattr(node.func, "id", None)
        if func_name in ALLOWED_FUNCTIONS and len(node.args) == 1:
            return ALLOWED_FUNCTIONS[func_name](_eval_node(node.args[0]))
        raise ValueError("Неизвестная функция")

    raise ValueError("Неразрешённая конструкция")


def safe_eval(expression: str):
    """
    Принимает строку вида "(1+2)*sin(pi/2)" и возвращает число.
    SyntaxError — если строка вообще не похожа на выражение,
    ValueError — если в дереве встретилось что-то запрещённое.
    """
    if not expression:
        raise ValueError("Пустое выражение")
    tree = ast.parse(expression, mode="eval")     # строка → дерево операций
    return _eval_node(tree)


def format_result(value) -> str:
    """
    Красиво печатает число: 3.0 → "3", а 1.2246467991473532e-16 → "0".
    .12g — «до 12 значимых цифр», этого хватает, чтобы убрать шум
    двоичных дробей после, например, sin(pi).
    """
    return f"{value:.12g}"


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
    except ValueError as e:
        # math доменные ошибки: sqrt(-4), ln(0), log(-10)
        if "domain error" in str(e).lower():
            return jsonify({"error": "Недопустимое значение: √ только от ≥0, логарифм только от >0"}), 400
        return jsonify({"error": "Некорректное выражение"}), 400
    except SyntaxError:
        return jsonify({"error": "Некорректное выражение"}), 400

    # Сохраняем каждое вычисление в базу данных
    formatted = format_result(result)
    with get_db() as db:
        db.execute(
            "INSERT INTO history (expression, result, created_at) VALUES (?, ?, ?)",
            (expression, formatted, datetime.now().isoformat(timespec="seconds")),
        )

    return jsonify({"expression": expression, "result": formatted})


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
