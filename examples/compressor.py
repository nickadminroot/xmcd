"""Connected compressor calculation using constructions from textbook pp. 112–116.

The kinematic parameters and pressure samples follow the supplied pages. All
functions, differentiation, interpolation, integration and plots execute in
Mathcad. Python only constructs the worksheet.
"""

from pathlib import Path

from xmcd import (
    Derivative,
    Function,
    If,
    Integral,
    Matrix,
    Otherwise,
    Program,
    Range,
    ResultFormat,
    Symbol,
    Trace,
    Worksheet,
    f,
)


def build():
    sheet = Worksheet("Compressor mechanism", tolerance=1e-6)
    phi, q, z = (Symbol(n) for n in ("φ", "q", "z"))
    pi, deg = Symbol("π"), Symbol("deg")
    l1, l2 = Symbol("l1"), Symbol("l2")
    probe = Symbol("probe")
    sheet.text("Компрессор: кинематика, инерция, давление и работа", top=24, style="Heading 1")
    sheet.text("По конструкциям и исходным данным страниц 112–116.")
    for name, value in {
        "Vavg": 3.2,
        "n1": 10,
        "ratio": 4,
        "mass2": 8,
        "mass3": 10,
        "J2": 0.22,
        "gravity": 10,
        "diameter": 0.2,
        "pmax": 500000,
    }.items():
        sheet.define(name, value)
    sheet.define(l1, Symbol("Vavg") / (4 * Symbol("n1")), tag="input-crank-length")
    sheet.define(l2, Symbol("ratio") * l1)
    sheet.define("center", 0.33 * l2)
    sheet.define(probe, 120 * deg)
    sheet.evaluate(l1, tag="crank-0.08")
    sheet.evaluate(l2, tag="rod-0.32")
    sheet.text("Положение и кинематические передаточные функции", style="Heading 2")
    functions = {
        "phi1": pi / 2 - phi,
        "xB": l1 * f.cos(f.phi1(phi)),
        "yB": l1 * f.sin(f.phi1(phi)),
        "phi2": f.acos(-f.xB(phi) / l2),
        "yC": f.yB(phi) + l2 * f.sin(f.phi2(phi)),
        "xS": f.xB(phi) + Symbol("center") * f.cos(f.phi2(phi)),
        "yS": f.yB(phi) + Symbol("center") * f.sin(f.phi2(phi)),
    }
    for name, value in functions.items():
        sheet.define(Function(name, [phi]), value, height=36)
    for position in ("xB", "yB", "yC", "xS", "yS", "phi2"):
        sheet.define(Function("v_" + position, [phi]), Derivative(f[position](phi), phi), height=45)
        sheet.define(
            Function("a_" + position, [phi]), Derivative(f[position](phi), phi, degree=2), height=50
        )
    for name in ("xB", "yB", "yC", "xS", "yS", "v_yC", "a_yC", "v_phi2", "a_phi2"):
        sheet.evaluate(f[name](probe), tag="probe-" + name)
    sheet.define("X", Matrix.vector([0, f.xB(probe), f.xS(probe), 0]), height=70)
    sheet.define("Y", Matrix.vector([0, f.yB(probe), f.yS(probe), f.yC(probe)]), height=70)
    sheet.define(phi, Range(0, 2 * pi, second=0.05))
    sheet.plot(
        Trace("X", "Y", color="#000000"),
        Trace(f.xB(phi), f.yB(phi), color="#ff0000"),
        Trace(f.xS(phi), f.yS(phi), color="#0000ff"),
        left=30,
        width=340,
        height=270,
        tag="mechanism-and-trajectories",
    )
    sheet.plot(
        Trace(phi / deg, f.v_yC(phi)),
        Trace(phi / deg, f.a_yC(phi)),
        left=30,
        width=360,
        height=240,
        tag="velocity-acceleration",
    )
    sheet.text("Приведённый момент инерции", style="Heading 2")
    inertia = (
        Symbol("J2") * f.v_phi2(phi) ** 2
        + Symbol("mass2") * (f.v_xS(phi) ** 2 + f.v_yS(phi) ** 2)
        + Symbol("mass3") * f.v_yC(phi) ** 2
    )
    sheet.define(Function("inertia", [phi]), inertia, height=48)
    sheet.evaluate(f.inertia(probe), tag="inertia-at-probe")
    sheet.text("Табличная индикаторная диаграмма и давление", style="Heading 2")
    sheet.define("sbc", Matrix.vector([0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1]), height=130)
    sheet.define("pbc", Matrix.vector([1, 0.58, 0.38, 0.26, 0.18, 0.12, 0.07, 0.03, 0]), height=130)
    sheet.define("sad", Matrix.vector([0, 0.1, 0.2]), height=55)
    sheet.define("pad", Matrix.vector([1, 0.3, 0]), height=55)
    sheet.define("cbc", f.lspline("sbc", "pbc"))
    sheet.define("cad", f.lspline("sad", "pad"))
    sheet.define(
        Function("PBC", [z]),
        Program(If(z < 0.2, 1), Otherwise(f.interp("cbc", "sbc", "pbc", z))),
        height=65,
    )
    sheet.define(
        Function("PAD", [z]),
        Program(If(z > 0.2, 0), Otherwise(f.interp("cad", "sad", "pad", z))),
        height=65,
    )
    sheet.define(Function("stroke", [phi]), (f.yC(0) - f.yC(phi)) / (2 * l1), height=42)
    sheet.define(
        Function("pressure", [phi]),
        Program(
            If(f.v_yC(phi) > 0, Symbol("pmax") * f.PBC(f.stroke(phi))),
            Otherwise(Symbol("pmax") * f.PAD(f.stroke(phi))),
        ),
        height=75,
    )
    sheet.define(
        Function("force", [phi]), -f.pressure(phi) * pi * Symbol("diameter") ** 2 / 4, height=42
    )
    moment = (
        f.force(phi) * f.v_yC(phi)
        - Symbol("mass2") * Symbol("gravity") * f.v_yS(phi)
        - Symbol("mass3") * Symbol("gravity") * f.v_yC(phi)
    )
    sheet.define(Function("moment", [phi]), moment, height=42)
    for name in ("stroke", "pressure", "force", "moment"):
        sheet.evaluate(f[name](probe), tag="probe-" + name)
    sheet.define(Function("work", [phi]), Integral(f.moment(q), q, 0, phi), height=55)
    sheet.evaluate(f.work(2 * pi), tag="cycle-work", height=35)
    sheet.evaluate(-f.work(2 * pi) / (2 * pi), tag="mean-driving-moment", height=42)
    sheet.plot(
        Trace(phi / deg, f.pressure(phi)), left=30, width=360, height=240, tag="pressure-cycle"
    )
    sheet.plot(Trace(phi / deg, f.moment(phi)), left=30, width=360, height=240, tag="moment-cycle")
    sheet.text("Таблица: угол, положение, скорость, ускорение, сила", style="Heading 2")
    i, table = Symbol("i"), Symbol("results")
    sheet.define(i, Range(0, 12))
    for column, value in enumerate(
        (
            i * 30,
            f.yC(i * 30 * deg),
            f.v_yC(i * 30 * deg),
            f.a_yC(i * 30 * deg),
            f.force(i * 30 * deg),
        )
    ):
        sheet.define(table[i, column], value, height=36)
    sheet.evaluate(
        table, result_format=ResultFormat(matrix_style="table"), height=240, tag="mechanism-table"
    )
    return sheet


if __name__ == "__main__":
    Path("output").mkdir(exist_ok=True)
    print(build().write("output/compressor.xmcd"))
