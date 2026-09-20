"""Connected compressor calculation using constructions from textbook pp. 112–116.

The kinematic parameters and pressure samples follow the supplied pages. All
functions, differentiation, interpolation, integration and plots execute in
Mathcad. Python only constructs the worksheet.
"""

from pathlib import Path

from xmcd import (
    BuiltinFunction,
    Derivative,
    Function,
    If,
    Integral,
    Matrix,
    MatrixStyle,
    Otherwise,
    Program,
    Range,
    ResultFormat,
    Symbol,
    TextStyle,
    Trace,
    Worksheet,
)


def build():
    sheet = Worksheet("Compressor mechanism", tolerance=1e-6)
    phi, q, z = (Symbol(n) for n in ("φ", "q", "z"))
    pi, deg = Symbol("π"), Symbol("deg")
    l1, l2 = Symbol("l1"), Symbol("l2")
    probe = Symbol("probe")
    sheet.text(
        "Компрессор: кинематика, инерция, давление и работа", top=24, style=TextStyle.HEADING_1
    )
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
        sheet.define(Symbol(name), value)
    sheet.define(l1, Symbol("Vavg") / (4 * Symbol("n1")), tag="input-crank-length")
    sheet.define(l2, Symbol("ratio") * l1)
    sheet.define(Symbol("center"), 0.33 * l2)
    sheet.define(probe, 120 * deg)
    sheet.evaluate(l1, tag="crank-0.08")
    sheet.evaluate(l2, tag="rod-0.32")
    sheet.text("Положение и кинематические передаточные функции", style=TextStyle.HEADING_2)
    functions = {
        "phi1": pi / 2 - phi,
        "xB": l1 * BuiltinFunction.COS(Symbol("phi1")(phi)),
        "yB": l1 * BuiltinFunction.SIN(Symbol("phi1")(phi)),
        "phi2": BuiltinFunction.ACOS(-Symbol("xB")(phi) / l2),
        "yC": Symbol("yB")(phi) + l2 * BuiltinFunction.SIN(Symbol("phi2")(phi)),
        "xS": Symbol("xB")(phi) + Symbol("center") * BuiltinFunction.COS(Symbol("phi2")(phi)),
        "yS": Symbol("yB")(phi) + Symbol("center") * BuiltinFunction.SIN(Symbol("phi2")(phi)),
    }
    for name, value in functions.items():
        sheet.define(Function(Symbol(name), [phi]), value, height=36)
    for position in ("xB", "yB", "yC", "xS", "yS", "phi2"):
        sheet.define(
            Function(Symbol("v_" + position), [phi]),
            Derivative(Symbol(position)(phi), phi),
            height=45,
        )
        sheet.define(
            Function(Symbol("a_" + position), [phi]),
            Derivative(Symbol(position)(phi), phi, degree=2),
            height=50,
        )
    for name in ("xB", "yB", "yC", "xS", "yS", "v_yC", "a_yC", "v_phi2", "a_phi2"):
        sheet.evaluate(Symbol(name)(probe), tag="probe-" + name)
    sheet.define(
        Symbol("X"), Matrix.vector([0, Symbol("xB")(probe), Symbol("xS")(probe), 0]), height=70
    )
    sheet.define(
        Symbol("Y"),
        Matrix.vector([0, Symbol("yB")(probe), Symbol("yS")(probe), Symbol("yC")(probe)]),
        height=70,
    )
    sheet.define(phi, Range(0, 2 * pi, second=0.05))
    sheet.plot(
        Trace(Symbol("X"), Symbol("Y"), color="#000000"),
        Trace(Symbol("xB")(phi), Symbol("yB")(phi), color="#ff0000"),
        Trace(Symbol("xS")(phi), Symbol("yS")(phi), color="#0000ff"),
        left=30,
        width=340,
        height=270,
        tag="mechanism-and-trajectories",
    )
    sheet.plot(
        Trace(phi / deg, Symbol("v_yC")(phi)),
        Trace(phi / deg, Symbol("a_yC")(phi)),
        left=30,
        width=360,
        height=240,
        tag="velocity-acceleration",
    )
    sheet.text("Приведённый момент инерции", style=TextStyle.HEADING_2)
    inertia = (
        Symbol("J2") * Symbol("v_phi2")(phi) ** 2
        + Symbol("mass2") * (Symbol("v_xS")(phi) ** 2 + Symbol("v_yS")(phi) ** 2)
        + Symbol("mass3") * Symbol("v_yC")(phi) ** 2
    )
    sheet.define(Function(Symbol("inertia"), [phi]), inertia, height=48)
    sheet.evaluate(Symbol("inertia")(probe), tag="inertia-at-probe")
    sheet.text("Табличная индикаторная диаграмма и давление", style=TextStyle.HEADING_2)
    sheet.define(
        Symbol("sbc"), Matrix.vector([0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1]), height=130
    )
    sheet.define(
        Symbol("pbc"), Matrix.vector([1, 0.58, 0.38, 0.26, 0.18, 0.12, 0.07, 0.03, 0]), height=130
    )
    sheet.define(Symbol("sad"), Matrix.vector([0, 0.1, 0.2]), height=55)
    sheet.define(Symbol("pad"), Matrix.vector([1, 0.3, 0]), height=55)
    sheet.define(Symbol("cbc"), BuiltinFunction.LSPLINE(Symbol("sbc"), Symbol("pbc")))
    sheet.define(Symbol("cad"), BuiltinFunction.LSPLINE(Symbol("sad"), Symbol("pad")))
    sheet.define(
        Function(Symbol("PBC"), [z]),
        Program(
            If(z < 0.2, 1),
            Otherwise(BuiltinFunction.INTERP(Symbol("cbc"), Symbol("sbc"), Symbol("pbc"), z)),
        ),
        height=65,
    )
    sheet.define(
        Function(Symbol("PAD"), [z]),
        Program(
            If(z > 0.2, 0),
            Otherwise(BuiltinFunction.INTERP(Symbol("cad"), Symbol("sad"), Symbol("pad"), z)),
        ),
        height=65,
    )
    sheet.define(
        Function(Symbol("stroke"), [phi]),
        (Symbol("yC")(0) - Symbol("yC")(phi)) / (2 * l1),
        height=42,
    )
    sheet.define(
        Function(Symbol("pressure"), [phi]),
        Program(
            If(Symbol("v_yC")(phi) > 0, Symbol("pmax") * Symbol("PBC")(Symbol("stroke")(phi))),
            Otherwise(Symbol("pmax") * Symbol("PAD")(Symbol("stroke")(phi))),
        ),
        height=75,
    )
    sheet.define(
        Function(Symbol("force"), [phi]),
        -Symbol("pressure")(phi) * pi * Symbol("diameter") ** 2 / 4,
        height=42,
    )
    moment = (
        Symbol("force")(phi) * Symbol("v_yC")(phi)
        - Symbol("mass2") * Symbol("gravity") * Symbol("v_yS")(phi)
        - Symbol("mass3") * Symbol("gravity") * Symbol("v_yC")(phi)
    )
    sheet.define(Function(Symbol("moment"), [phi]), moment, height=42)
    for name in ("stroke", "pressure", "force", "moment"):
        sheet.evaluate(Symbol(name)(probe), tag="probe-" + name)
    sheet.define(
        Function(Symbol("work"), [phi]), Integral(Symbol("moment")(q), q, 0, phi), height=55
    )
    sheet.evaluate(Symbol("work")(2 * pi), tag="cycle-work", height=35)
    sheet.evaluate(-Symbol("work")(2 * pi) / (2 * pi), tag="mean-driving-moment", height=42)
    sheet.plot(
        Trace(phi / deg, Symbol("pressure")(phi)),
        left=30,
        width=360,
        height=240,
        tag="pressure-cycle",
    )
    sheet.plot(
        Trace(phi / deg, Symbol("moment")(phi)), left=30, width=360, height=240, tag="moment-cycle"
    )
    sheet.text("Таблица: угол, положение, скорость, ускорение, сила", style=TextStyle.HEADING_2)
    i, table = Symbol("i"), Symbol("results")
    sheet.define(i, Range(0, 12))
    for column, value in enumerate(
        (
            i * 30,
            Symbol("yC")(i * 30 * deg),
            Symbol("v_yC")(i * 30 * deg),
            Symbol("a_yC")(i * 30 * deg),
            Symbol("force")(i * 30 * deg),
        )
    ):
        sheet.define(table[i, column], value, height=36)
    sheet.evaluate(
        table,
        result_format=ResultFormat(matrix_style=MatrixStyle.TABLE),
        height=240,
        tag="mechanism-table",
    )
    return sheet


if __name__ == "__main__":
    Path("output").mkdir(exist_ok=True)
    print(build().write("output/compressor.xmcd"))
