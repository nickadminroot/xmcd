"""Arithmetic plot expressions and native point marker styles."""

from pathlib import Path

from xmcd import Range, Symbol, Trace, Worksheet


def build():
    w = Worksheet("Plot expressions and markers")
    t = Symbol("t")
    w.define(t, Range(-3, 3, second=-2.9))
    w.plot(
        Trace(t, (t + 1) * (t - 2), marker="circle"),
        Trace(t, -t, style="dash"),
        left=70,
        width=350,
        height=250,
        x_grid=True,
        y_grid=True,
        tag="compound-operators",
    )
    w.text("Маркеры: крест, плюс, квадрат, ромб, круг, треугольник; четыре залитых фигуры.")
    markers = [
        "cross",
        "plus",
        "square",
        "diamond",
        "circle",
        "triangle",
        "filled-square",
        "filled-diamond",
        "filled-circle",
        "filled-triangle",
    ]
    w.plot(
        *(Trace(i, 0, marker=marker, color="#000000") for i, marker in enumerate(markers, 1)),
        left=70,
        width=390,
        height=260,
        x_bounds=(0, 11),
        y_bounds=(-1, 1),
        tag="point-markers",
    )
    return w


if __name__ == "__main__":
    Path("output").mkdir(exist_ok=True)
    print(build().write("output/plot_expressions.xmcd"))
