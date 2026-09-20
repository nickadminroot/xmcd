# xmcd

Python-библиотека для создания документов Mathcad XML (XMCD) без установленного Mathcad и Windows COM.

Объектная модель выражений, регионов и листов. Целевой формат: классический Mathcad, не Mathcad Prime MCDX.

Проект находится в разработке. [Покрытие и проверка](docs/compatibility.md) отделяют реализованные возможности от подтверждённых в Mathcad.

## Использование

```bash
uv sync
uv run python examples/core.py
uv run pytest -q
```

```python
from xmcd import Worksheet, Symbol, Function, Matrix, Integral, f

x = Symbol("x")
sheet = Worksheet("Расчёт")
sheet.text("Пример расчёта", top=24)
sheet.define(Function("g", [x]), x**3 + 2*x)
sheet.evaluate(f.g(2))
sheet.define("M", Matrix([[1, 2], [3, 4]]), height=50)
sheet.evaluate(Integral(x**2, x, 0, 1), height=50)
sheet.write("example.xmcd")
```

Строка в выражении обозначает идентификатор; для строкового значения используйте `String`. Матрицы задаются строками Python. `Symbol("x", subscript="A")` — буквенный индекс, `x[i]` — обращение к элементу массива. `x.eq(y)` создаёт равенство Mathcad; условия не преобразуются в Python `bool`.

`f` позволяет вызывать встроенные и пользовательские функции по имени без конечного списка разрешённых функций. Наличие вызова в XMCD не подтверждает корректность его аргументов: вычисление выполняет Mathcad при открытии документа.

Размеры регионов и координаты задаются в пунктах. `sheet.add(region)` сохраняет явное положение; `sheet.math(...)` и `sheet.text(...)` размещают следующий регион ниже предыдущего, если `top` не задан. Для высоких формул задавайте `height`: библиотека пока не измеряет их типографскую высоту.
