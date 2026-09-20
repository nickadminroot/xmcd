# Python API

Все публичные классы импортируются из `xmcd`. Генератор строит документ; вычисления выполняет Mathcad. Выражения можно вкладывать и повторно использовать, а документы собирать циклами и функциями Python.

## Лист и размещение

`Worksheet(title='', author='', origin=0, tolerance=1e-3, constraint_tolerance=1e-3, page=PageSettings(), result_format=ResultFormat(), font_size=10)`.

| Метод | Назначение |
|---|---|
| `add(region)` | Добавить регион с явными координатами |
| `text(text, **layout)` | Текст; перенос строки создаёт абзац |
| `math(expression, **layout)` | Математическое поле |
| `define(lhs, rhs, **layout)` | Обычное определение `:=` |
| `evaluate(expression, unit=None, **layout)` | Вычисление `=` и необязательная единица результата |
| `plot(*traces, **layout)` / `polar_plot(...)` | Редактируемый график |
| `to_xml()` / `to_bytes()` / `write(path)` | Дерево lxml, XML-байты или запись файла |

`layout`: `left`, `top`, `width`, `height` в пунктах, `tag`, `border`. Без `top` методы размещают следующий регион ниже предыдущего с отступом 12 pt. `add` сохраняет явные координаты. Выделяйте достаточную высоту матрицам, интегралам, программам и таблицам: автоматического измерения формул нет. Родительский каталог для `write` должен существовать.

`TextRegion(text, style='Normal', **layout)` поддерживает стили `Normal`, `Heading 1`, `Heading 2`. `MathRegion(expression, result_format=None, disabled=False, **layout)` позволяет отдельно настроить результат или отключить пересчёт поля. `PageBreak(**layout)` вставляет разрыв страницы.

`Area(name, regions, collapsed=False, **layout)` объединяет регионы. Координаты дочерних регионов задаются относительно области; её высоту задавайте с учётом содержимого. Свёрнутая область сохраняет определения и участвует в расчёте.

`PageSettings` задаёт `paper_code` (код Windows, A4 = 9), `orientation` (`portrait` / `landscape`) и поля `margin_left/right/top/bottom` в пунктах. `ResultFormat(precision=6, notation='general', matrix_style='matrix')`: notation — `general`, `decimal`, `scientific`, `engineering`, `fraction`; matrix_style — `auto`, `matrix`, `table`. Табличный вывод остаётся редактируемым результатом Mathcad.

## Выражения

| Конструкция | Пример |
|---|---|
| Число, мнимая часть, строка | `Number(2)`, `Imaginary(3)`, `String('текст')` |
| Идентификатор, буквенный индекс | `Symbol('x')`, `Symbol('F', subscript='12x')` |
| Преобразование Python-значения | `expr(2 + 3j)`; строка превращается в `Symbol` |
| Арифметика | `x + 2`, `2*x`, `x/y`, `x**2`, `-x`, `abs(x)` |
| Сравнения | `x.eq(y)`, `x.ne(y)`, `x < y`, `x >= y` |
| Логика | `(x > 0) & (x < 1)`, `a | b`, `~a` |
| Функция и вызов | `Function('g', [x])`, `f.sin(x)`, `f['имя'](x)` |
| Матрица и столбец | `Matrix([[1, 2], [3, 4]])`, `Matrix.vector([1, 2])` |
| Индексы | `A[i, j]`, `v[i]`, `A.column(j)`, `A.row(i)` |
| Операции с матрицами | `A.T`, `A.determinant()`, `(A*B).vectorize()` |
| Радикалы и логарифм | `x.sqrt()`, `x.nth_root(5)`, `x.log(2)` |
| Сопряжение, факториал | `x.conjugate()`, `x.factorial()` |
| Скобки | `Parens(x + 1)` или `(x + 1).parens()` |
| Диапазон | `Range(0, 1, second=0.1)` |

В `Range` параметр `second` — второе значение, а не шаг: диапазон от 5 с шагом 0.1 задаётся `Range(5, 10, second=5.1)`. Индексы Mathcad отсчитываются от `Worksheet.origin`. Матрицы передаются строками Python; порядок хранения XML библиотека преобразует сама.

`==` и `!=` не создают формулы Mathcad: используйте `.eq()` / `.ne()`. Вместо Python `and/or/not` используйте `&/|/~` со скобками. Преобразование выражения в `bool` запрещено. Скобки, необходимые для сохранения порядка вычисления, сериализатор добавляет автоматически.

`Operator(name, *arguments)` предоставляет именованные операции. Унарные: `absval`, `conjugate`, `factorial`, `neg`, `not`, `sqrt`, `transpose`, `vectorize`, `vectorSum`, `determinant`. Бинарные: `and`, `crossProduct`, `div`, `equal`, `greaterOrEqual`, `greaterThan`, `indexer`, `lessOrEqual`, `lessThan`, `log`, `matrow`, `matcol`, `minus`, `mult`, `notEqual`, `nthRoot`, `or`, `plus`, `pow`, `xor`. Для `log` порядок — основание, аргумент; для `nthRoot` — степень корня, подкоренное выражение. `matrow` реализован через транспонирование и извлечение столбца, поскольку прямой узел не читается проверенной версией Mathcad.

`Sequence(a, b, ...)` — последовательность аргументов, `Placeholder()` — редактируемое пустое место. `Call(function, *arguments)` эквивалентен вызову выражения `function(...)`.

## Определения, анализ и решатели

- `Define(lhs, rhs, kind='normal')`; варианты `local` для программ и `global` для определения, видимого выше по листу.
- `Evaluate(expression, unit=None)`; `Symbolic(expression, commands=('factor',))` создаёт символьную стрелку. Аргумент команды: `commands=(('collect', x),)`.
- `Derivative(expression, variable, degree=1)`; `Integral(expression, variable, lower=None, upper=None)`; `Sum` и `Product` с теми же аргументами. Указывайте обе границы либо ни одной; неопределённый интеграл предназначен для символьного вычисления.
- `Given()` начинает решающий блок. Начальные приближения размещаются выше, ограничения — после `Given`, завершающий вызов — после ограничений.
- `Solver('Find')(x, y)`, `Solver('Minerr')(x)`, `Solver('Minimize')(objective, x)`, `Solver('Maximize')(objective, x)`, `Solver('Odesolve')(t, end)`.

`Solver` принимает необязательный `method`: `linear`, `conjugate`, `newton`, `quadratic`, `levenberg`; для `Odesolve` — `fixed`, `adaptive`, `radau`, `adams/bdf (auto)`. Пригодность метода зависит от задачи; живые примеры проверяют автоматический выбор.

Пространство `f` открыто: `f.linterp`, `f.lspline`, `f.pspline`, `f.cspline`, `f.interp`, `f.lsolve`, `f.augment`, `f.stack`, `f.Rkadapt` и другие вызовы записываются без белого списка. Это не Python-реализации вычислителей; имена и аргументы должны соответствовать установленному Mathcad. Квадратный корень задавайте `.sqrt()`, а не `f.sqrt`.

## Программы

`Program(*statements)` содержит не менее двух строк. Строками могут быть выражения, `Define(..., kind='local')`, `If(condition, value)`, `Otherwise(value)`, `For(variable, values, body)`, `While(condition, body)`, `Return(value)`, `Break()`, `Continue()`, `TryCatch(expression, fallback)`. Тело цикла или ветви может быть вложенной программой.

```python
from xmcd import Function, Program, If, Otherwise, Symbol, Worksheet

x = Symbol('x')
sheet = Worksheet()
sheet.define(Function('positive', [x]), Program(If(x > 0, x), Otherwise(0)), height=60)
sheet.evaluate(Function('positive', [x])(-2))
sheet.write('program.xmcd')
```

## Графики и проверка

`Trace(x, y, color=None, style='solid', marker='none')`, `XYPlot(traces, **layout)` и `PolarPlot(traces, **layout)` описаны в [справочнике графиков](plot-format.md). Там же перечислен поддержанный поднабор выражений непосредственно внутри графика.

`validate(path_or_bytes, schema=None)` проверяет структуру и ссылки, а при передаче локальной XSD — схему; ошибки выбрасываются как `ValidationError`. `calculation_errors(path_or_bytes)` читает сохранённые Mathcad ошибки и возвращает `CalculationError`. Ни одна из этих функций не пересчитывает документ. Проверяйте сохранённые результаты и сообщения аудитора; отсутствие `error` само по себе недостаточно.

[Совместимость и результаты пересчёта](compatibility.md), [покрытие книги](book-coverage.md). Исходные примеры в `examples/` содержат готовые сочетания всех основных конструкций.
