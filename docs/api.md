# Python API

Все публичные классы импортируются из `xmcd`. API принимает явные объекты и перечисления. Строковые сокращения не поддерживаются: вместо `define("x", 1)` используйте `define(Symbol("x"), 1)`. Строки в позициях выражений вызывают `TypeError`; числовые литералы преобразуются в `Number`. Генератор строит документ; вычисления выполняет Mathcad. Выражения можно вкладывать и повторно использовать, а документы собирать циклами и функциями Python.

## Лист и размещение

`Worksheet(title='', author='', origin=0, tolerance=1e-3, constraint_tolerance=1e-3, page=PageSettings(), result_format=ResultFormat(), font_size=10)`.

| Метод | Назначение |
|---|---|
| `add(region)` | Добавить регион с автоматическим или явным размещением |
| `text(text, **layout)` | Текст; перенос строки создаёт абзац |
| `math(expression, **layout)` | Математическое поле |
| `define(lhs, rhs, **layout)` | Обычное определение `:=` |
| `evaluate(expression, unit=None, **layout)` | Вычисление `=` и необязательная единица результата |
| `plot(*traces, **layout)` / `polar_plot(...)` | Редактируемый график |
| `to_xml()` / `to_bytes()` / `write(path)` | Дерево lxml, XML-байты или запись файла |

`layout`: `left`, `top`, `width`, `height` в пунктах, `tag`, `border`. При `top=None` регион размещается автоматически; при `height=None` его высота оценивается с запасом. Это относится и к `add(region)`. Перед сериализацией поток пересчитывается, поэтому изменение формулы сдвигает следующие автоматические регионы. Явные координаты и высота сохраняются. [Правила и ограничения размещения](layout.md). Родительский каталог для `write` должен существовать.

`TextRegion(text, style=TextStyle.NORMAL, **layout)` поддерживает стили `TextStyle.NORMAL`, `TextStyle.HEADING_1`, `TextStyle.HEADING_2`. `MathRegion(expression, result_format=None, disabled=False, result_shape=None, **layout)` позволяет отдельно настроить результат или отключить пересчёт поля. `PageBreak(**layout)` вставляет разрыв страницы.

`Area(name, regions, collapsed=False, **layout)` объединяет регионы. Координаты дочерних регионов задаются относительно области; её высота без явного значения определяется по содержимому. Свёрнутая область сохраняет определения и участвует в расчёте.

`PageSettings` задаёт `paper_code` (код Windows, A4 = 9), `orientation` (`Orientation.PORTRAIT` / `Orientation.LANDSCAPE`) и поля `margin_left/right/top/bottom` в пунктах. `ResultFormat(precision=6, notation=NumberFormat.GENERAL, matrix_style=MatrixStyle.MATRIX)`: `notation` принимает `NumberFormat`, `matrix_style` — `MatrixStyle`. Табличный вывод остаётся редактируемым результатом Mathcad.

## Выражения

| Конструкция | Пример |
|---|---|
| Число, мнимая часть, строка | `Number(2)`, `Imaginary(3)`, `String('текст')` |
| Идентификатор, буквенный индекс | `Symbol('x')`, `Symbol('F', subscript=LiteralSubscript('12x'))` |
| Преобразование Python-значения | `expr(2 + 3j)`; строки не принимаются |
| Арифметика | `x + 2`, `2*x`, `x/y`, `x**2`, `-x`, `abs(x)` |
| Сравнения | `x.eq(y)`, `x.ne(y)`, `x < y`, `x >= y` |
| Логика | `(x > 0) & (x < 1)`, `a | b`, `~a` |
| Функция и вызов | `Function(Symbol('g'), [x])`, `BuiltinFunction.SIN(x)`, `Symbol('имя')(x)` |
| Матрица и столбец | `Matrix([[1, 2], [3, 4]])`, `Matrix.vector([1, 2])` |
| Индексы | `A[i, j]`, `v[i]`, `A.column(j)`, `A.row(i)` |
| Операции с матрицами | `A.T`, `A.determinant()`, `(A*B).vectorize()` |
| Радикалы и логарифм | `x.sqrt()`, `x.nth_root(5)`, `x.log(2)` |
| Сопряжение, факториал | `x.conjugate()`, `x.factorial()` |
| Скобки | `Parens(x + 1)` или `(x + 1).parens()` |
| Диапазон | `Range(0, 1, second=0.1)` |

В `Range` параметр `second` — второе значение, а не шаг: диапазон от 5 с шагом 0.1 задаётся `Range(5, 10, second=5.1)`. Индексы Mathcad отсчитываются от `Worksheet.origin`. Матрицы передаются строками Python; порядок хранения XML библиотека преобразует сама.

`==` и `!=` не создают формулы Mathcad: используйте `.eq()` / `.ne()`. Вместо Python `and/or/not` используйте `&/|/~` со скобками. Преобразование выражения в `bool` запрещено. Скобки, необходимые для сохранения порядка вычисления, сериализатор добавляет автоматически.

`Operator(kind, *arguments)` принимает `OperatorKind`, например `Operator(OperatorKind.CROSS_PRODUCT, a, b)` или `Operator(OperatorKind.VECTOR_SUM, v)`. Перечисление охватывает арифметику, сравнения, логику, радикалы и матричные операции. Для `LOG` порядок — основание, аргумент; для `NTH_ROOT` — степень корня, подкоренное выражение. `ROW` реализован через транспонирование и извлечение столбца, поскольку прямой узел `matrow` не читается проверенной версией Mathcad.

`Sequence(a, b, ...)` — последовательность аргументов, `Placeholder()` — редактируемое пустое место. `Call(function, *arguments)` эквивалентен вызову выражения `function(...)`.

## Определения, анализ и решатели

- `Define(lhs, rhs, kind=DefinitionKind.NORMAL)`; варианты `DefinitionKind.LOCAL` для программ и `DefinitionKind.GLOBAL` для определения, видимого выше по листу.
- `Evaluate(expression, unit=None)`; `Symbolic(expression, commands=(Symbol('factor'),))` создаёт символьную стрелку. Аргумент команды: `commands=(Sequence(Symbol('collect'), x),)`.
- `Derivative(expression, variable, degree=1)`; `Integral(expression, variable, lower=None, upper=None)`; `Sum` и `Product` с теми же аргументами. Указывайте обе границы либо ни одной; неопределённый интеграл предназначен для символьного вычисления.
- `Given()` начинает решающий блок. Начальные приближения размещаются выше, ограничения — после `Given`, завершающий вызов — после ограничений.
- `Solver(SolverKind.FIND)(x, y)`, `Solver(SolverKind.MINERR)(x)`, `Solver(SolverKind.MINIMIZE)(objective, x)`, `Solver(SolverKind.MAXIMIZE)(objective, x)`, `Solver(SolverKind.ODESOLVE)(t, end)`.

`Solver` принимает необязательный `method: SolverMethod`: `LINEAR`, `CONJUGATE`, `NEWTON`, `QUADRATIC`, `LEVENBERG`; для `ODESOLVE` — `FIXED`, `ADAPTIVE`, `RADAU`, `ADAMS_BDF`. Пригодность метода зависит от задачи; живые примеры проверяют автоматический выбор.

Встроенные функции представлены `BuiltinFunction`: например, `BuiltinFunction.LINTERP`, `BuiltinFunction.LSOLVE`, `BuiltinFunction.RKADAPT`. Для остальных встроенных и пользовательских функций используйте `Symbol("имя")(аргументы)` — без ограничения реестром. Имена и аргументы должны соответствовать установленному Mathcad. Квадратный корень задавайте `.sqrt()`. Пространство сокращений `f` удалено.

## Программы

`Program(*statements)` содержит не менее двух строк. Строками могут быть выражения, `Define(..., kind=DefinitionKind.LOCAL)`, `If(condition, value)`, `Otherwise(value)`, `For(variable, values, body)`, `While(condition, body)`, `Return(value)`, `Break()`, `Continue()`, `TryCatch(expression, fallback)`. Тело цикла или ветви может быть вложенной программой.

```python
from xmcd import Function, Program, If, Otherwise, Symbol, Worksheet

x = Symbol('x')
sheet = Worksheet()
sheet.define(Function(Symbol('positive'), [x]), Program(If(x > 0, x), Otherwise(0)), height=60)
sheet.evaluate(Function(Symbol('positive'), [x])(-2))
sheet.write('program.xmcd')
```

## Графики и проверка

`Trace(x, y, color=None, style=LineStyle.SOLID, marker=Marker.NONE)`, `XYPlot(traces, **layout)` и `PolarPlot(traces, **layout)` описаны в [справочнике графиков](plot-format.md). Там же перечислен поддержанный поднабор выражений непосредственно внутри графика.

`validate(path_or_bytes, schema=None)` проверяет структуру и ссылки, а при передаче локальной XSD — схему; ошибки выбрасываются как `ValidationError`. `calculation_errors(path_or_bytes)` читает сохранённые Mathcad ошибки и возвращает `CalculationError`. Ни одна из этих функций не пересчитывает документ. Проверяйте сохранённые результаты и сообщения аудитора; отсутствие `error` само по себе недостаточно.

[Совместимость и результаты пересчёта](compatibility.md), [покрытие книги](book-coverage.md). Исходные примеры в `examples/` содержат готовые сочетания всех основных конструкций.

## Типизированное оформление и имена

```python
from xmcd import BuiltinFunction as B, Greek, LiteralSubscript, Symbol

phi = Symbol(Greek.PHI, subscript=LiteralSubscript("12"))
omega = Symbol(Greek.OMEGA, subscript=LiteralSubscript(Greek.THETA))
expression = B.SIN(phi) + omega**2
```

`LiteralSubscript` является частью имени переменной: `φ₁₂` отличается от элемента `φ[12]`. Верхняя степень выражается `phi**2`. Греческие буквы можно выбирать через `Greek` (24 строчные и 24 прописные) или передавать Unicode в `Symbol`; автоматической замены латинского `alpha` на `α` нет. Строковые значения формул создаются через `String`, а имена — через `Symbol`. `Function(Symbol('g'), [x])` описывает функцию, этот же объект можно вызывать `g(x)`.

`BuiltinFunction` содержит распространённые встроенные функции и вызывается непосредственно: `BuiltinFunction.LSOLVE(A, b)`. Остальные встроенные и пользовательские функции доступны через `Symbol('имя')(...)`; реестр не ограничивает Mathcad.

Перечисления: `OperatorKind`, `SolverKind`, `SolverMethod`, `DefinitionKind`, `MatrixStyle`, `NumberFormat`, `LineStyle`, `Marker`, `TextStyle`, `Orientation`. Например, `Solver(SolverKind.FIND)`, `Operator(OperatorKind.CROSS_PRODUCT, a, b)`, `ResultFormat(matrix_style=MatrixStyle.TABLE)`, `Trace(x, y, marker=Marker.CIRCLE)`. Имена переменных, текст, подписи и HEX-цвета остаются текстовыми данными. Дочерние узлы выражений нормализуются в объекты `Expr` при создании: например, `Define(x, 2).rhs` — `Number`. Аннотации и `py.typed` включены в пакет.
