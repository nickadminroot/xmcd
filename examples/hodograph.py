"""Polar reaction hodograph and a vector showing one chosen state."""

from pathlib import Path

from xmcd import BuiltinFunction, Function, Matrix, Range, Symbol, Trace, Worksheet


def build():
    sheet = Worksheet("Polar hodograph")
    t = Symbol("t")
    sheet.text("Polar hodograph: angle and reaction magnitude", top=24)
    sheet.define(Function(Symbol("Fx"), [t]), 2 + BuiltinFunction.COS(t))
    sheet.define(Function(Symbol("Fy"), [t]), BuiltinFunction.SIN(t))
    sheet.define(
        Function(Symbol("direction"), [t]), BuiltinFunction.ANGLE(Symbol("Fx")(t), Symbol("Fy")(t))
    )
    sheet.define(
        Function(Symbol("magnitude"), [t]), (Symbol("Fx")(t) ** 2 + Symbol("Fy")(t) ** 2).sqrt()
    )
    sheet.define(Symbol("angle_vector"), Matrix.vector([0, Symbol("direction")(1)]), height=45)
    sheet.define(Symbol("radius_vector"), Matrix.vector([0, Symbol("magnitude")(1)]), height=45)
    sheet.evaluate(Symbol("magnitude")(1), tag="magnitude-at-1")
    sheet.define(t, Range(0, 2 * Symbol("π"), second=0.03))
    sheet.polar_plot(
        Trace(Symbol("direction")(t), Symbol("magnitude")(t), color="#0000ff"),
        Trace(Symbol("angle_vector"), Symbol("radius_vector"), color="#ff0000"),
        left=30,
        width=360,
        height=340,
        y_bounds=(0, 3.5),
        tag="hodograph",
    )
    return sheet


if __name__ == "__main__":
    Path("output").mkdir(exist_ok=True)
    print(build().write("output/hodograph.xmcd"))
