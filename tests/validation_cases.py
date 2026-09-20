"""Native comparison worksheet with deliberately invalid and valid regions."""

from xmcd import BuiltinFunction as B
from xmcd import Function, Matrix, Number, Solver, SolverKind, Symbol, Worksheet


def build():
    w = Worksheet("Static validation comparison")
    w.text("Deliberately invalid formulas followed by valid controls")
    cases = {
        "undefined-symbol": Symbol("missing_validation_variable") + 1,
        "function-arity": B.SIN(1, 2),
        "matrix-dimensions": Matrix([[1, 2, 3], [4, 5, 6]]) * Matrix([[1, 2], [3, 4]]),
        "index-bounds": Matrix([[1, 2], [3, 4]])[2, 0],
        "unit-mismatch": Symbol("m") + Symbol("s"),
        "division-by-zero": Number(1) / 0,
    }
    for tag, expression in cases.items():
        w.text(tag)
        w.evaluate(expression, height=65, tag=tag)
    w.evaluate(Matrix.vector([1, 2, 3]) * Matrix.vector([1, 2, 3]), height=55, tag="valid-dot-14")
    w.evaluate(Number(2.5).factorial(), height=55, tag="factorial-probe")
    x = Symbol("x")
    cost = Function(Symbol("cost"), [x])
    w.define(cost, (x - 3) ** 2)
    w.define(x, 1)
    w.evaluate(Solver(SolverKind.MINIMIZE)(cost.name, x), height=55, tag="valid-minimum-3")
    return w
