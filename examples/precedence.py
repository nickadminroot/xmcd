"""Native regression cases for Mathcad visual operator precedence."""

from pathlib import Path

from xmcd import Matrix, Worksheet
from xmcd import Number as N


def build():
    w = Worksheet("Operator grouping")
    a, b, c = N(2), N(3), N(4)
    checks = {
        "multiply-sum": a * (b + c),
        "sum-multiply": (a + b) * c,
        "minus-sum": a - (b + c),
        "minus-minus": a - (b - c),
        "negative-sum": -(a + b),
        "power-sum": (a + b) ** c,
        "power-power": (a**b) ** c,
        "power-exponent": a ** (b + c),
        "negative-base": N(-2) ** 2,
        "negative-expression": (-a) ** 2,
        "factorial-sum": (a + b).factorial(),
        "fraction-sum": (a + b) / (c + a),
        "nested-fraction": a / (b / c),
        "boolean": (a < b) & (b < c),
        "sqrt": (a + b).sqrt(),
        "transpose": (Matrix([[1, 2], [3, 4]]) + Matrix([[4, 3], [2, 1]])).T,
    }
    for tag, e in checks.items():
        w.evaluate(e, tag=tag, height=60)
    return w


if __name__ == "__main__":
    Path("output").mkdir(exist_ok=True)
    print(build().write("output/precedence.xmcd"))
