"""Cam synthesis from textbook pp. 133–136, calculated entirely in Mathcad."""

from pathlib import Path

from xmcd import Function, Given, Integral, Matrix, Range, Solver, Symbol, Trace, Worksheet, f


def build():
    w = Worksheet("Cam with translating roller follower", tolerance=1e-6)
    t, q, y = (Symbol(n) for n in ("t", "q", "y"))
    pi, deg, h, am1, am2 = (Symbol(n) for n in ("π", "deg", "h", "am1", "am2"))
    fu, fc, fr, fd = (Symbol(n) for n in ("fu", "fc", "fr", "fd"))
    p1, p2, p3, p4, p5 = (Symbol("p" + str(i)) for i in range(1, 6))
    s0, e, theta = (Symbol(n) for n in ("s0", "e", "theta_max"))
    w.text("Кулачок с поступательным роликовым толкателем", top=24, style="Heading 1")
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
        "knots",
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
    w.define("velocity_knots", Matrix.vector([0, p1, p2, p3, p4, p5, 2 * pi]), height=120)
    for stage in ("unit", "normalized"):
        w.text(
            "Единичные ускорения" if stage == "unit" else "Нормировка на заданный ход",
            style="Heading 2",
        )
        if stage == "normalized":
            w.define(am1, am1 * h / f.s(fu), height=40)
            w.define(am2, am2 * h / (f.s(fu) - f.s(fr)), height=40)
        w.define(
            "acceleration_values",
            Matrix.vector([0, am1, am1, -am1, -am1, 0, 0, -am2, -am2, am2, am2, 0, 0]),
            height=220,
        )
        w.define(Function("a", [t]), f.linterp("knots", "acceleration_values", t))
        w.define(Function("integrated_v", [t]), Integral(f.a(q), q, 0, t), height=52)
        w.define(
            "velocity_values",
            Matrix.vector([0, f.integrated_v(p1), 0, 0, f.integrated_v(p4), 0, 0]),
            height=130,
        )
        w.define(Function("v", [t]), f.linterp("velocity_knots", "velocity_values", t))
        w.define(Function("s", [t]), Integral(f.v(q), q, 0, t), height=52)
        w.evaluate(f.s(130 * deg), tag=stage + "-lift")
        w.evaluate(f.s(2 * pi), tag=stage + "-closure")
    w.define(t, Range(0, 2 * pi, second=0.02))
    for name in ("a", "v", "s"):
        w.plot(Trace(t / deg, f[name](t)), width=380, height=220, left=30, tag="cam-" + name)
    w.text("Радиус и смещение: решающий блок", style="Heading 2")
    w.define(s0, h)
    w.define(e, 0)
    w.math(Given())
    w.math(f.tan(theta).eq((f.v(p1) + e) / (s0 + f.s(p1))), height=50)
    w.math(f.tan(theta).eq((-f.v(p4) - e) / (s0 + f.s(p4))), height=50)
    w.define("solution", Solver("Find")(s0, e), height=42)
    w.define(s0, Symbol("solution")[0])
    w.define(e, Symbol("solution")[1])
    w.define("r0", (s0**2 + e**2).sqrt(), height=42)
    for name in ("s0", "e", "r0"):
        w.evaluate(name, tag="cam-" + name)
    w.define(Function("pressure_angle", [t]), f.atan((f.v(t) + e) / (s0 + f.s(t))), height=52)
    w.evaluate(f.pressure_angle(p1) / deg, tag="pressure-plus30")
    w.evaluate(f.pressure_angle(p4) / deg, tag="pressure-minus30")
    w.define(Function("tangent_left", [y]), -e - f.tan(theta) * (y + s0))
    w.define(Function("tangent_right", [y]), -e + f.tan(theta) * (y + s0))
    w.define(y, Range(-s0, h, second=-s0 + 0.001))
    w.plot(
        Trace(f.v(t), f.s(t)),
        Trace(f.tangent_left(y), y, style="dash"),
        Trace(f.tangent_right(y), y, style="dash"),
        left=30,
        width=350,
        height=310,
        tag="cam-phase-portrait",
    )
    w.plot(
        Trace(t / deg, f.pressure_angle(t) / deg),
        left=30,
        width=380,
        height=220,
        tag="cam-pressure-angle",
    )
    w.text("Центровой и конструктивный профили, ролик и толкатель", style="Heading 2")
    w.define("roller_radius", 0.01)
    w.define("position", 0 * deg)
    pos, r = Symbol("position"), Symbol("roller_radius")
    functions = {
        "xA": e * f.cos(t),
        "yA": e * f.sin(t),
        "xB": f.xA(t) + s0 * f.cos(t + pi / 2),
        "yB": f.yA(t) + s0 * f.sin(t + pi / 2),
        "xC": f.xB(t) + f.s(t) * f.cos(t + pi / 2),
        "yC": f.yB(t) + f.s(t) * f.sin(t + pi / 2),
        "xD": f.xC(t) - r * f.cos(t + pi / 2 - f.pressure_angle(t)),
        "yD": f.yC(t) - r * f.sin(t + pi / 2 - f.pressure_angle(t)),
        "xR": f.xC(pos) + r * f.cos(t),
        "yR": f.yC(pos) + r * f.sin(t),
    }
    for name, value in functions.items():
        w.define(Function(name, [t]), value, height=38)
    w.define("X", Matrix.vector([f.xC(pos), f.xC(pos) - h * f.sin(pos)]), height=50)
    w.define("Y", Matrix.vector([f.yC(pos), f.yC(pos) + h * f.cos(pos)]), height=50)
    w.plot(
        *(
            Trace(f["x" + n](t), f["y" + n](t), style=style)
            for n, style in [
                ("A", "dot"),
                ("B", "dash-dot"),
                ("C", "dash"),
                ("D", "solid"),
                ("R", "solid"),
            ]
        ),
        Trace("X", "Y"),
        left=30,
        width=400,
        height=390,
        tag="cam-profile",
    )
    w.evaluate(f.xD(0), tag="profile-x0")
    w.evaluate(f.yD(0), tag="profile-y0")
    return w


if __name__ == "__main__":
    Path("output").mkdir(exist_ok=True)
    print(build().write("output/cam.xmcd"))
