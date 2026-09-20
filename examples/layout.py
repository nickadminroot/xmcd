"""Automatic conservative layout: no manual top/height for content regions."""

from pathlib import Path

from xmcd import (
    BuiltinFunction as B,
)
from xmcd import (
    Function,
    Greek,
    If,
    Integral,
    LiteralSubscript,
    Marker,
    Matrix,
    MatrixStyle,
    Number,
    Otherwise,
    Program,
    Range,
    ResultFormat,
    Symbol,
    TextStyle,
    Trace,
    Worksheet,
)


def build(font_size=10):
    w = Worksheet("Automatic layout and typed notation", font_size=font_size)
    x = Symbol("x")
    alpha = Symbol(Greek.ALPHA)
    phi = Symbol(Greek.PHI, subscript=LiteralSubscript("12"))
    omega = Symbol(Greek.OMEGA, subscript=LiteralSubscript(Greek.THETA))
    w.text("Автоматическая высота: формулы, матрицы и таблицы", style=TextStyle.HEADING_1)
    w.text("Длинный текст должен переноситься по ширине поля. " * 8, width=240, tag="wrapped-text")
    w.define(x, 2)
    w.define(alpha, 3)
    w.define(phi, 5)
    w.define(omega, 7)
    w.evaluate(alpha + phi + omega, tag="greek-15")
    fraction = (x + 1 / (x + 2 / (x + 3))) / (1 + (x**2 + 1) / (x + 1))
    w.evaluate(fraction, tag="nested-fraction")
    w.text("Текст после многоэтажной дроби", tag="after-fraction")
    matrix = Matrix(
        [
            [Number(r + 1) / (c + 1), Number(r + c + 2).sqrt(), (x + r) ** (c + 1)]
            for r, c in enumerate(range(8))
        ]
    )
    a = Symbol("A")
    w.define(a, matrix, tag="tall-matrix")
    w.evaluate(a, tag="matrix-result")
    w.evaluate(a[2, 0], tag="indexed-1")
    w.evaluate(a, result_format=ResultFormat(matrix_style=MatrixStyle.TABLE), tag="result-table")
    w.text("Текст после таблицы", tag="after-table")
    g = Function(Symbol("g"), [x])
    w.define(g, Program(If(x > 0, fraction), Otherwise(x**2)), tag="program")
    w.evaluate(g(2), tag="program-result")
    w.evaluate(Integral(x**2, x, 0, 1), tag="integral-third")
    t = Symbol(Greek.THETA)
    w.define(t, Range(0, 6.2, second=0.1))
    w.plot(
        Trace(t, B.SIN(t), marker=Marker.CIRCLE), Trace(t, B.COS(t)), width=340, tag="first-graph"
    )
    w.plot(Trace(B.COS(t), B.SIN(t)), width=340, tag="second-graph")
    w.text("Конец документа", tag="after-graphs")
    return w


if __name__ == "__main__":
    Path("output").mkdir(exist_ok=True)
    print(build().write("output/layout.xmcd"))
    print(build(14).write("output/layout-14.xmcd"))
