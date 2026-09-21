"""Conservative placement of range-evaluation tables and following text."""

from pathlib import Path

from xmcd import (
    BuiltinFunction as B,
)
from xmcd import (
    Function,
    Matrix,
    MatrixStyle,
    Number,
    Range,
    ResultFormat,
    Symbol,
    Worksheet,
)


def build(font_size=10):
    w = Worksheet("Range result tables", font_size=font_size)
    t, k, j = Symbol("t"), Symbol("k"), Symbol("j")
    grid, values = Symbol("grid"), Symbol("values")
    g = Function(Symbol("g"), [t])
    constant = Function(Symbol("constant"), [t])
    w.text("Автоматическое размещение табличных результатов")
    w.define(grid, Matrix.vector([0, 1, 2]))
    w.define(values, Matrix.vector([0, 1, 4]))
    w.define(g, B.LINTERP(grid, values, t))
    w.define(constant, 7)
    w.define(k, Range(0, 2, second=0.1))
    w.evaluate(g(k), tag="interpolation-table")
    w.text("Текст после интерполяционной таблицы", tag="after-interpolation")
    w.evaluate(constant(k), tag="constant-table")
    w.text("Текст после постоянной функции на диапазоне", tag="after-constant")
    w.define(Symbol("stop"), Number(4).sqrt())
    w.define(k, Range(0, Symbol("stop"), second=0.1))
    w.evaluate(g(k), tag="unknown-length-table")
    w.text("Текст после диапазона с неизвестной анализатору длиной", tag="after-unknown")
    w.define(j, Range(0, 2))
    w.evaluate(values[j], tag="indexed-table")
    w.text("Текст после таблицы индексированных значений", tag="after-indexed")
    w.evaluate(
        values, result_format=ResultFormat(matrix_style=MatrixStyle.TABLE), tag="explicit-table"
    )
    w.text("Текст после явного табличного вывода матрицы", tag="after-explicit")
    return w


if __name__ == "__main__":
    Path("output").mkdir(exist_ok=True)
    print(build().write("output/range_tables.xmcd"))
