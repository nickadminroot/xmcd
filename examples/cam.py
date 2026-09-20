"""Cam synthesis from textbook pp. 133–136, calculated entirely in Mathcad."""

from pathlib import Path

from xmcd import (
    BuiltinFunction,
    Function,
    Given,
    Integral,
    LineStyle,
    Matrix,
    Range,
    Solver,
    SolverKind,
    Symbol,
    TextStyle,
    Trace,
    Worksheet,
)


def build():
    w = Worksheet("Cam with translating roller follower", tolerance=1e-6)
    t, q, y = (Symbol(n) for n in ("t", "q", "y"))
    pi, deg, h, am1, am2 = (Symbol(n) for n in ("π", "deg", "h", "am1", "am2"))
    fu, fc, fr, fd = (Symbol(n) for n in ("fu", "fc", "fr", "fd"))
    p1, p2, p3, p4, p5 = (Symbol("p" + str(i)) for i in range(1, 6))
    s0, e, theta = (Symbol(n) for n in ("s0", "e", "theta_max"))
    w.text("Кулачок с поступательным роликовым толкателем", top=24, style=TextStyle.HEADING_1)
    w.text("Расчёт по конструкциям страниц 133–136; длины в метрах, углы в радианах.")
    for name, value in [
        (h, 0.015),
        (theta, 30 * deg),
        (fr, 220 * deg),
        (fu, 115 * deg),
        (fc, 75 * deg),
        (fd, fr - fu - fc),
        (p1, fu / 2),
        (p2, fu),
        (p3, fu + fd),
        (p4, fu + fd + fc / 2),
        (p5, fr),
        (am1, 1),
        (am2, 1),
    ]:
        w.define(name, value, height=32)
    w.define(
        Symbol("knots"),
        Matrix.vector(
            [
                0,
                0.0001,
                p1,
                p1 + 0.0001,
                p2,
                p2 + 0.0001,
                p3,
                p3 + 0.0001,
                p4,
                p4 + 0.0001,
                p5,
                p5 + 0.0001,
                2 * pi,
            ]
        ),
        height=220,
    )
    w.define(Symbol("velocity_knots"), Matrix.vector([0, p1, p2, p3, p4, p5, 2 * pi]), height=120)
    for stage in ("unit", "normalized"):
        w.text(
            "Единичные ускорения" if stage == "unit" else "Нормировка на заданный ход",
            style=TextStyle.HEADING_2,
        )
        if stage == "normalized":
            w.define(am1, am1 * h / Symbol("s")(fu), height=40)
            w.define(am2, am2 * h / (Symbol("s")(fu) - Symbol("s")(fr)), height=40)
        w.define(
            Symbol("acceleration_values"),
            Matrix.vector([0, am1, am1, -am1, -am1, 0, 0, -am2, -am2, am2, am2, 0, 0]),
            height=220,
        )
        w.define(
            Function(Symbol("a"), [t]),
            BuiltinFunction.LINTERP(Symbol("knots"), Symbol("acceleration_values"), t),
        )
        w.define(
            Function(Symbol("integrated_v"), [t]), Integral(Symbol("a")(q), q, 0, t), height=52
        )
        w.define(
            Symbol("velocity_values"),
            Matrix.vector([0, Symbol("integrated_v")(p1), 0, 0, Symbol("integrated_v")(p4), 0, 0]),
            height=130,
        )
        w.define(
            Function(Symbol("v"), [t]),
            BuiltinFunction.LINTERP(Symbol("velocity_knots"), Symbol("velocity_values"), t),
        )
        w.define(Function(Symbol("s"), [t]), Integral(Symbol("v")(q), q, 0, t), height=52)
        w.evaluate(Symbol("s")(130 * deg), tag=stage + "-lift")
        w.evaluate(Symbol("s")(2 * pi), tag=stage + "-closure")
    w.define(t, Range(0, 2 * pi, second=0.02))
    for name in ("a", "v", "s"):
        w.plot(Trace(t / deg, Symbol(name)(t)), width=380, height=220, left=30, tag="cam-" + name)
    w.text("Радиус и смещение: решающий блок", style=TextStyle.HEADING_2)
    w.define(s0, h)
    w.define(e, 0)
    w.math(Given())
    w.math(BuiltinFunction.TAN(theta).eq((Symbol("v")(p1) + e) / (s0 + Symbol("s")(p1))), height=50)
    w.math(
        BuiltinFunction.TAN(theta).eq((-Symbol("v")(p4) - e) / (s0 + Symbol("s")(p4))), height=50
    )
    w.define(Symbol("solution"), Solver(SolverKind.FIND)(s0, e), height=42)
    w.define(s0, Symbol("solution")[0])
    w.define(e, Symbol("solution")[1])
    w.define(Symbol("r0"), (s0**2 + e**2).sqrt(), height=42)
    for name in ("s0", "e", "r0"):
        w.evaluate(Symbol(name), tag="cam-" + name)
    w.define(
        Function(Symbol("pressure_angle"), [t]),
        BuiltinFunction.ATAN((Symbol("v")(t) + e) / (s0 + Symbol("s")(t))),
        height=52,
    )
    w.evaluate(Symbol("pressure_angle")(p1) / deg, tag="pressure-plus30")
    w.evaluate(Symbol("pressure_angle")(p4) / deg, tag="pressure-minus30")
    w.define(Function(Symbol("tangent_left"), [y]), -e - BuiltinFunction.TAN(theta) * (y + s0))
    w.define(Function(Symbol("tangent_right"), [y]), -e + BuiltinFunction.TAN(theta) * (y + s0))
    w.define(y, Range(-s0, h, second=-s0 + 0.001))
    w.plot(
        Trace(Symbol("v")(t), Symbol("s")(t)),
        Trace(Symbol("tangent_left")(y), y, style=LineStyle.DASH),
        Trace(Symbol("tangent_right")(y), y, style=LineStyle.DASH),
        left=30,
        width=350,
        height=310,
        tag="cam-phase-portrait",
    )
    w.plot(
        Trace(t / deg, Symbol("pressure_angle")(t) / deg),
        left=30,
        width=380,
        height=220,
        tag="cam-pressure-angle",
    )
    w.text("Центровой и конструктивный профили, ролик и толкатель", style=TextStyle.HEADING_2)
    w.define(Symbol("roller_radius"), 0.01)
    w.define(Symbol("position"), 0 * deg)
    pos, r = Symbol("position"), Symbol("roller_radius")
    functions = {
        "xA": e * BuiltinFunction.COS(t),
        "yA": e * BuiltinFunction.SIN(t),
        "xB": Symbol("xA")(t) + s0 * BuiltinFunction.COS(t + pi / 2),
        "yB": Symbol("yA")(t) + s0 * BuiltinFunction.SIN(t + pi / 2),
        "xC": Symbol("xB")(t) + Symbol("s")(t) * BuiltinFunction.COS(t + pi / 2),
        "yC": Symbol("yB")(t) + Symbol("s")(t) * BuiltinFunction.SIN(t + pi / 2),
        "xD": Symbol("xC")(t) - r * BuiltinFunction.COS(t + pi / 2 - Symbol("pressure_angle")(t)),
        "yD": Symbol("yC")(t) - r * BuiltinFunction.SIN(t + pi / 2 - Symbol("pressure_angle")(t)),
        "xR": Symbol("xC")(pos) + r * BuiltinFunction.COS(t),
        "yR": Symbol("yC")(pos) + r * BuiltinFunction.SIN(t),
    }
    for name, value in functions.items():
        w.define(Function(Symbol(name), [t]), value, height=38)
    w.define(
        Symbol("X"),
        Matrix.vector([Symbol("xC")(pos), Symbol("xC")(pos) - h * BuiltinFunction.SIN(pos)]),
        height=50,
    )
    w.define(
        Symbol("Y"),
        Matrix.vector([Symbol("yC")(pos), Symbol("yC")(pos) + h * BuiltinFunction.COS(pos)]),
        height=50,
    )
    w.plot(
        *(
            Trace(Symbol("x" + n)(t), Symbol("y" + n)(t), style=style)
            for n, style in [
                ("A", LineStyle.DOT),
                ("B", LineStyle.DASH_DOT),
                ("C", LineStyle.DASH),
                ("D", LineStyle.SOLID),
                ("R", LineStyle.SOLID),
            ]
        ),
        Trace(Symbol("X"), Symbol("Y")),
        left=30,
        width=400,
        height=390,
        tag="cam-profile",
    )
    w.evaluate(Symbol("xD")(0), tag="profile-x0")
    w.evaluate(Symbol("yD")(0), tag="profile-y0")
    return w


if __name__ == "__main__":
    Path("output").mkdir(exist_ok=True)
    print(build().write("output/cam.xmcd"))
