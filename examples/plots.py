"""Editable function graphs and a parametric trajectory, generated without Mathcad."""

from pathlib import Path

from xmcd import Range, Symbol, Trace, Worksheet, f


def build():
    sheet = Worksheet("Native XY graphs")
    t = Symbol("t")
    sheet.text("Native plots: functions and parametric trajectory", top=24)
    sheet.define(t, Range(0, 6.28, second=0.02))
    sheet.plot(
        Trace(t, f.sin(t), color="#ff0000"),
        Trace(t, f.cos(t), color="#0000ff"),
        Trace(t, t / 10, color="#008000", style="dash"),
        top=110,
        left=30,
        width=360,
        height=240,
        tag="functions",
    )
    sheet.plot(
        Trace(f.cos(t), f.sin(t), color="#800080"),
        top=410,
        left=30,
        width=320,
        height=280,
        tag="trajectory",
        x_bounds=(-1.2, 1.2),
        y_bounds=(-1.2, 1.2),
    )
    return sheet


if __name__ == "__main__":
    Path("output").mkdir(exist_ok=True)
    print(build().write("output/plots.xmcd"))
