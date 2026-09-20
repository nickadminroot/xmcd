# xmcd

Python-библиотека для создания документов Mathcad XML (XMCD) без установленного Mathcad и Windows COM.

Объектная модель выражений, регионов и листов. Целевой формат: классический Mathcad, не Mathcad Prime MCDX.

Версия 0.3: формулы, матрицы, программы, решающие блоки, редактируемые XY- и полярные графики. [Покрытие и проверка](docs/compatibility.md) отделяют реализованные возможности от подтверждённых в Mathcad.

## Использование

```bash
uv sync
uv run python examples/core.py
uv run pytest -q
```

```python
from xmcd import Worksheet, Symbol, Function, Matrix, Integral

x = Symbol("x")
sheet = Worksheet("Расчёт")
sheet.text("Пример расчёта", top=24)
g = Function(Symbol("g"), [x])
sheet.define(g, x**3 + 2*x)
sheet.evaluate(g(2))
sheet.define(Symbol("M"), Matrix([[1, 2], [3, 4]]))
sheet.evaluate(Integral(x**2, x, 0, 1))
sheet.write("example.xmcd")
```

API использует явные объекты: `Symbol`, `Number`, `String`, `Function`, `Matrix`, `BuiltinFunction`. Настройки и операции имеют перечисления: `SolverKind`, `OperatorKind`, `DefinitionKind`, `MatrixStyle`, `LineStyle`, `Marker`. `Greek` задаёт греческие буквы, `LiteralSubscript` — буквенный индекс. Числовой индекс массива задаётся `A[i, j]`. Строки в позициях выражений и вместо перечислений не принимаются; используйте `Symbol("x")` для имени и `String("текст")` для строкового значения. Числовые литералы поддерживаются. Примеры — в [справочнике API](docs/api.md).

Высота формул, матриц и текста оценивается автоматически с запасом. Последовательные регионы размещаются ниже предыдущего; для графиков резервируется место под подписи. Можно явно задать `top` и `height`. Размер вычисляемой матрицы определяется по известным определениям; если он неизвестен без пересчёта, передайте `result_shape=ResultShape(rows, columns)`. См. [правила размещения](docs/layout.md) и `examples/layout.py`.

`Worksheet.write()` автоматически проверяет документ до записи: доступность имён, аргументы функций, известные размеры и индексы матриц, ряд числовых ошибок и совместимость известных единиц. `sheet.check()` возвращает диагностику; ошибки вызывают `WorksheetValidationError`. Сходимость и произвольные вычисления требуют Mathcad. [Проверки, строгий режим и ограничения](docs/validation.md).

Решающие блоки: `Given()` и `Solver(SolverKind.FIND)(x, y)`, пример `examples/solvers.py`. Редактируемые графики: `Trace`, `XYPlot` и `sheet.plot(...)`; [примеры и ограничения](docs/plot-format.md).

[Справочник Python API](docs/api.md) · [Карта покрытия страниц книги](docs/book-coverage.md).

## Установка пакета

```bash
uv build
uv pip install dist/xmcd-0.3.0-py3-none-any.whl
```

Пакет не обращается к Windows, Mathcad или COM. Для вычисления формул полученный файл открывается в классическом Mathcad. Проверенная версия — 14.1.5.594; совместимость с другими версиями требует отдельного тестирования.

Связанные расчёты: `examples/compressor.py` и `examples/cam.py`. Остальные примеры показывают отдельные группы API. Сгенерированные файлы записываются в `output/`; пересчитанные образцы для регрессии находятся в `tests/fixtures/`.
