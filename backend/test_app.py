# Тесты калькулятора: python3 -m unittest discover -v
#
# Проверяем две вещи:
#   1. safe_eval — чистая логика вычислений (скобки, тригонометрия, π)
#   2. /api/calculate — HTTP-маршрут целиком: запрос → ответ → запись в базу
#
# Для тестов поднимаем Flask-приложение с временной базой в памяти,
# поэтому боевой calculator.db не пострадает.

import math
import os
import tempfile
import unittest

# Указываем базе данных временный файл ДО импорта приложения
# (app.py читает переменную окружения прямо при загрузке модуля)
_tmpdb = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["DATABASE_FILE"] = _tmpdb.name

import app as calc  # noqa: E402 — импорт после настройки окружения


class TestSafeEval(unittest.TestCase):
    """Юнит-тесты вычислителя — без HTTP и базы."""

    # --- Арифметика и приоритеты ---
    def test_basic_arithmetic(self):
        self.assertEqual(calc.safe_eval("7+2"), 9)
        self.assertEqual(calc.safe_eval("10-4*2"), 2)     # приоритет: умножение раньше
        self.assertEqual(calc.safe_eval("12/4"), 3)
        self.assertEqual(calc.safe_eval("-5+3"), -2)

    # --- Скобки (главная цель этой доработки) ---
    def test_brackets(self):
        self.assertEqual(calc.safe_eval("(1+2)*3"), 9)
        self.assertEqual(calc.safe_eval("2*(3+4)"), 14)
        self.assertEqual(calc.safe_eval("(2+3)*(4-1)"), 15)          # несколько групп
        self.assertEqual(calc.safe_eval("((1+2)*(3+4))/7"), 3)       # вложенные скобки
        self.assertEqual(calc.safe_eval("10/(5-3)"), 5)
        self.assertEqual(calc.safe_eval("-(3+2)"), -5)               # минус перед скобкой

    # --- Тригонометрия и π (углы в радианах) ---
    def test_trigonometry(self):
        self.assertEqual(calc.safe_eval("sin(0)"), 0)
        self.assertAlmostEqual(calc.safe_eval("sin(pi/2)"), 1)
        self.assertAlmostEqual(calc.safe_eval("cos(0)"), 1)
        self.assertAlmostEqual(calc.safe_eval("cos(pi)"), -1)
        self.assertAlmostEqual(calc.safe_eval("tan(pi/4)"), 1)
        # скобки внутри функции и функция в арифметике
        self.assertAlmostEqual(calc.safe_eval("2*sin(pi/2)+cos(0)"), 3)

    def test_pi_constant(self):
        self.assertAlmostEqual(calc.safe_eval("pi"), 3.14159265358979)
        self.assertAlmostEqual(calc.safe_eval("pi*2"), 6.28318530717959)

    # --- Корни ---
    def test_roots(self):
        self.assertEqual(calc.safe_eval("sqrt(9)"), 3)
        self.assertEqual(calc.safe_eval("sqrt(2)"), math.sqrt(2))
        self.assertEqual(calc.safe_eval("sqrt(0)"), 0)
        self.assertEqual(calc.safe_eval("cbrt(27)"), 3)
        self.assertAlmostEqual(calc.safe_eval("cbrt(-8)"), -2)        # кубический из отрицательного
        self.assertEqual(calc.safe_eval("sqrt(16)+cbrt(8)"), 6)       # две функции в выражении
        self.assertAlmostEqual(calc.safe_eval("sqrt(sqrt(16))"), 2)   # вложенные корни

    # --- Логарифмы ---
    def test_logarithms(self):
        self.assertEqual(calc.safe_eval("ln(1)"), 0)
        self.assertEqual(calc.safe_eval("log(1000)"), 3)
        self.assertEqual(calc.safe_eval("log(1)"), 0)
        self.assertAlmostEqual(calc.safe_eval("ln(pi)"), math.log(math.pi))
        # натуральный логарифм от e — это 1 (e ≈ 2.718281828459045 подставляем числом)
        self.assertAlmostEqual(calc.safe_eval("ln(2.718281828459045)"), 1)
        # связь логарифма и степени: log(10^4) = 4
        self.assertAlmostEqual(calc.safe_eval("log(10*10*10*10)"), 4)

    # --- Доменные ошибки: sqrt от отрицательного, логарифм от неположительного ---
    def test_domain_errors(self):
        with self.assertRaises(ValueError):
            calc.safe_eval("sqrt(-4)")
        with self.assertRaises(ValueError):
            calc.safe_eval("ln(0)")
        with self.assertRaises(ValueError):
            calc.safe_eval("log(-10)")

    # --- Отрицательные случаи: всё запрещённое должно ловиться ---
    def test_errors(self):
        with self.assertRaises(ValueError):
            calc.safe_eval("")                                   # пусто
        with self.assertRaises(SyntaxError):
            calc.safe_eval("2+2;import os")                      # мусор: парсер не пропускает ;
        with self.assertRaises(ValueError):
            calc.safe_eval("__import__('os')")                   # попытка вызвать «магию» Python
        with self.assertRaises(ValueError):
            calc.safe_eval("print(1)")                           # неизвестная функция
        with self.assertRaises(ValueError):
            calc.safe_eval("abs(-5)")                              # не добавляли — быть запрещено
        with self.assertRaises(SyntaxError):
            calc.safe_eval("(1+2")                               # незакрытая скобка
        with self.assertRaises(ZeroDivisionError):
            calc.safe_eval("5/0")

    def test_format_result(self):
        self.assertEqual(calc.format_result(3.0), "3")           # без хвостового .0
        self.assertEqual(calc.format_result(12246467991473532e-17)[:1], "0")  # шум float → "0"
        self.assertEqual(calc.format_result(2.5), "2.5")


class TestCalculateEndpoint(unittest.TestCase):
    """Интеграционные тесты HTTP-маршрута через тестовый клиент Flask."""

    def setUp(self):
        self.client = calc.app.test_client()
        with calc.get_db() as db:
            db.execute("DELETE FROM history")                    # чистим перед каждым тестом

    def post(self, expression):
        return self.client.post(
            "/api/calculate",
            json={"expression": expression},
        )

    def test_brackets_end_to_end(self):
        res = self.post("(1+2)*3")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["result"], "9")
        # вычисление сохранилось в истории
        history = self.client.get("/api/history").get_json()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["expression"], "(1+2)*3")

    def test_trig_end_to_end(self):
        res = self.post("sin(pi/2)")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["result"], "1")          # .12g прибирает float-шум

    def test_roots_and_logs_end_to_end(self):
        self.assertEqual(self.post("sqrt(144)").get_json()["result"], "12")
        self.assertEqual(self.post("cbrt(-27)").get_json()["result"], "-3")
        self.assertEqual(self.post("log(100)").get_json()["result"], "2")
        # доменная ошибка возвращается по-человечески
        res = self.post("sqrt(-4)")
        self.assertEqual(res.status_code, 400)
        self.assertIn("Недопустимое значение", res.get_json()["error"])

    def test_division_by_zero_returns_400(self):
        res = self.post("5/0")
        self.assertEqual(res.status_code, 400)
        self.assertIn("ноль", res.get_json()["error"].lower())

    def test_invalid_expression_returns_400(self):
        res = self.post("sin(pi")                                # незакрытая скобка
        self.assertEqual(res.status_code, 400)
        # в историю некорректное выражение не попадает
        self.assertEqual(self.client.get("/api/history").get_json(), [])

    def test_security_injection_blocked(self):
        res = self.post("__import__('os').system('echo hacked')")
        self.assertEqual(res.status_code, 400)


if __name__ == "__main__":
    unittest.main()
