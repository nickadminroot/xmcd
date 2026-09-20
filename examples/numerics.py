"""Book-related numerical primitives; every result is evaluated by Mathcad."""

from pathlib import Path

from xmcd import BuiltinFunction, Function, Matrix, MatrixStyle, ResultFormat, Symbol, Worksheet


def build():
    sheet = Worksheet("Numerical acceptance", tolerance=1e-7)
    x, t, y = (Symbol(n) for n in ("x", "t", "y"))
    grid = Symbol("grid")
    values = Symbol("values")
    sheet.text("Interpolation, matrices and differential equations", top=20)
    sheet.define(grid, Matrix.vector([0, 1, 2, 3]), height=65)
    sheet.define(values, Matrix.vector([0, 1, 4, 9]), height=65)
    sheet.evaluate(BuiltinFunction.LINTERP(grid, values, 1.5), tag="linear-2.5")
    for spline in ("lspline", "pspline", "cspline"):
        sheet.define(Symbol(spline + "_coef"), Symbol(spline)(grid, values), height=30)
        sheet.evaluate(
            BuiltinFunction.INTERP(Symbol(spline + "_coef"), grid, values, 1),
            tag=spline + "-knot-1",
        )
    a, b = Symbol("A"), Symbol("B")
    sheet.define(a, Matrix([[2, 1], [1, 3]]), height=45)
    sheet.define(b, Matrix.vector([5, 10]), height=45)
    sheet.define(Symbol("solution"), BuiltinFunction.LSOLVE(a, b))
    sheet.evaluate(Symbol("solution"), tag="linear-system-1-3", height=50)
    sheet.define(Symbol("wide"), BuiltinFunction.AUGMENT(a, a))
    sheet.define(Symbol("tall"), BuiltinFunction.STACK(a, a))
    sheet.evaluate(BuiltinFunction.COLS(Symbol("wide")), tag="augment-4")
    sheet.evaluate(BuiltinFunction.ROWS(Symbol("tall")), tag="stack-4")
    sheet.define(Symbol("elementwise"), (a * a).vectorize())
    sheet.evaluate(Symbol("elementwise")[1, 1], tag="vectorized-9")
    sheet.evaluate(a.T[0, 1], tag="transpose-1")
    sheet.evaluate(a.column(1)[1], tag="column-3")
    sheet.define(Symbol("zeros")[3, 3], 0)
    sheet.evaluate(BuiltinFunction.ROWS(Symbol("zeros")), tag="implicit-array-4")
    sheet.evaluate(BuiltinFunction.ROOT(x**2 - 2, x, 0, 2), tag="root-sqrt2")
    sheet.evaluate(BuiltinFunction.ANGLE(0, 1) / Symbol("deg"), tag="angle-90")
    # D has vector input/output; Mathcad supplies t and the current state y.
    sheet.define(Function(Symbol("D"), [t, y]), Matrix.vector([y[0]]), height=40)
    for solver in ("rkfixed", "Rkadapt"):
        sheet.define(
            Symbol(solver + "_solution"), Symbol(solver)(Matrix.vector([1]), 0, 1, 20, Symbol("D"))
        )
        sheet.evaluate(Symbol(solver + "_solution")[20, 1], tag=solver + "-e")
    sheet.evaluate(
        Symbol("Rkadapt_solution"),
        tag="ode-result-table",
        result_format=ResultFormat(matrix_style=MatrixStyle.TABLE),
        height=300,
    )
    sheet.evaluate(1000 * Symbol("mm"), unit=Symbol("m"), tag="units-meter")
    return sheet


if __name__ == "__main__":
    Path("output").mkdir(exist_ok=True)
    print(build().write("output/numerics.xmcd"))
