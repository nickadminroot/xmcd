"""Native constrained optimization and least-squares solve blocks."""

from pathlib import Path

from xmcd import Function, Given, Solver, SolverKind, Symbol, Worksheet


def build():
    sheet = Worksheet("Optimization acceptance", tolerance=1e-8, constraint_tolerance=1e-8)
    x = Symbol("x")
    sheet.text("Minimize, Maximize and Minerr", top=24)
    sheet.define(Function(Symbol("cost"), [x]), (x - 3) ** 2)
    sheet.define(x, 1)
    sheet.math(Given())
    sheet.math(x >= 0)
    sheet.define(Symbol("minimum"), Solver(SolverKind.MINIMIZE)(Symbol("cost"), x))
    sheet.evaluate(Symbol("minimum"), tag="minimum-3")
    sheet.define(Function(Symbol("benefit"), [x]), 10 - (x - 2) ** 2)
    sheet.define(x, 1)
    sheet.math(Given())
    sheet.math(x >= 0)
    sheet.define(Symbol("maximum"), Solver(SolverKind.MAXIMIZE)(Symbol("benefit"), x))
    sheet.evaluate(Symbol("maximum"), tag="maximum-2")
    sheet.define(x, 0)
    sheet.math(Given())
    sheet.math(x.eq(1))
    sheet.math(x.eq(3))
    sheet.define(Symbol("approximate"), Solver(SolverKind.MINERR)(x))
    sheet.evaluate(Symbol("approximate"), tag="minerr-2")
    return sheet


if __name__ == "__main__":
    Path("output").mkdir(exist_ok=True)
    print(build().write("output/optimization.xmcd"))
