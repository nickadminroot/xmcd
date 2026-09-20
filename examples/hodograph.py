"""Polar reaction hodograph and a vector showing one chosen state."""

from pathlib import Path

from xmcd import Function, Matrix, Range, Symbol, Trace, Worksheet, f


def build():
    sheet = Worksheet("Polar hodograph")
    t = Symbol("t")
    sheet.text("Polar hodograph: angle and reaction magnitude", top=24)
    sheet.define(Function("Fx", [t]), 2 + f.cos(t))
    sheet.define(Function("Fy", [t]), f.sin(t))
    sheet.define(Function("direction", [t]), f.angle(f.Fx(t), f.Fy(t)))
    sheet.define(Function("magnitude", [t]), (f.Fx(t) ** 2 + f.Fy(t) ** 2).sqrt())
    sheet.define("angle_vector", Matrix.vector([0, f.direction(1)]), height=45)
    sheet.define("radius_vector", Matrix.vector([0, f.magnitude(1)]), height=45)
    sheet.evaluate(f.magnitude(1), tag="magnitude-at-1")
    sheet.define(t, Range(0, 2 * Symbol("π"), second=0.03))
    sheet.polar_plot(
        Trace(f.direction(t), f.magnitude(t), color="#0000ff"),
        Trace("angle_vector", "radius_vector", color="#ff0000"),
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
