"""Remaining native mathematical operators, document areas and an ODE solve block."""

from pathlib import Path

from xmcd import (
    Area,
    BuiltinFunction,
    Define,
    DefinitionKind,
    Derivative,
    Given,
    MathRegion,
    Matrix,
    Number,
    Operator,
    OperatorKind,
    PageBreak,
    Product,
    Solver,
    SolverKind,
    String,
    Symbol,
    TextRegion,
    TextStyle,
    Worksheet,
    expr,
)


def build():
    w = Worksheet("Native operators and document structure")
    w.text("Области документа, математические операторы и ОДУ", top=24, style=TextStyle.HEADING_1)
    w.add(
        Area(
            "Вложенные определения",
            [
                TextRegion("Текст внутри области", top=30),
                MathRegion(Define(Symbol("a"), 5), top=65),
            ],
            top=90,
            height=135,
        )
    )
    w.add(
        Area(
            "Скрытые исходные данные",
            [MathRegion(Define(Symbol("hidden"), 13), top=30)],
            top=250,
            height=80,
            collapsed=True,
        )
    )
    w.evaluate(Symbol("hidden"), tag="hidden-value-13")
    w.evaluate(Symbol("a") + 2, tag="area-value-7")
    w.evaluate(Symbol("global_value"), tag="global-before-definition-11")
    w.math(Define(Symbol("global_value"), 11, kind=DefinitionKind.GLOBAL))
    w.define(Symbol("A"), Matrix([[1, 2], [3, 4]]), height=50)
    tests = {
        "row-1-2": Symbol("A").row(0),
        "cross-0-0-1": Operator(
            OperatorKind.CROSS_PRODUCT, Matrix.vector([1, 0, 0]), Matrix.vector([0, 1, 0])
        ),
        "vector-sum-6": Operator(OperatorKind.VECTOR_SUM, Matrix.vector([1, 2, 3])),
        "product-120": Product(Symbol("i"), Symbol("i"), 1, 5),
        "factorial-120": Number(5).factorial(),
        "fifth-root-2": Number(32).nth_root(5),
        "base2-log-3": Number(8).log(2),
        "complex-2-minus3i": expr(2 + 3j).conjugate(),
        "abs-5": abs(expr(3 + 4j)),
        "string-length-7": BuiltinFunction.STRLEN(String("Mathcad")),
    }
    for tag, value in tests.items():
        w.evaluate(value, tag=tag, height=65)
    w.add(PageBreak(top=w.regions[-1].top + 90, height=5))
    w.text("Решение y′ = y, y(0) = 1", style=TextStyle.HEADING_2)
    t = Symbol("t")
    w.math(Given())
    w.math(Derivative(Symbol("y")(t), t).eq(Symbol("y")(t)), height=50)
    w.math(Symbol("y")(0).eq(1))
    w.define(Symbol("y"), Solver(SolverKind.ODESOLVE)(t, 1), height=40)
    w.evaluate(Symbol("y")(1), tag="odesolve-e")
    return w


if __name__ == "__main__":
    Path("output").mkdir(exist_ok=True)
    print(build().write("output/advanced.xmcd"))
