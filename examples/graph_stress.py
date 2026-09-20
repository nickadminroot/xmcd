"""Graph formatting, a long function name and a tree with over 300 nodes."""

from pathlib import Path

from xmcd import Function, Range, Symbol, Trace, Worksheet, f


def build():
    w = Worksheet()
    t = Symbol("t")
    w.define(t, Range(0, 6.28, second=0.1))
    w.plot(
        Trace(t, f.sin(t), marker="circle"),
        left=70,
        width=320,
        height=230,
        tag="style-probe",
        x_grid=True,
        y_grid=True,
    )
    name = "u" + "a" * 69
    w.define(Function(name, [t]), f.sin(t))
    w.plot(Trace(t, f[name](t)), left=70, width=320, height=230, tag="name-70")
    w.plot(
        *(
            Trace(f.sin(f.sin(f.sin(f.sin(f.sin(t))))), f.cos(f.cos(f.cos(f.cos(f.cos(t))))))
            for _ in range(8)
        ),
        left=70,
        width=320,
        height=230,
        tag="tree-over-255",
    )
    return w


if __name__ == "__main__":
    Path("output").mkdir(exist_ok=True)
    print(build().write("output/graph_stress.xmcd"))
