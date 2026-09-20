"""Local assignment, loops, branching, exceptions and symbolic evaluation."""

from pathlib import Path

from xmcd import (
    Break,
    Continue,
    Define,
    For,
    Function,
    If,
    Otherwise,
    Program,
    Range,
    Return,
    Symbol,
    Symbolic,
    TryCatch,
    While,
    Worksheet,
)


def build():
    sheet = Worksheet("Programming acceptance")
    n, i, acc, x = (Symbol(s) for s in ("n", "i", "acc", "x"))

    def local(a, b):
        return Define(a, b, kind="local")

    sheet.text("Native Mathcad programming operators", top=20)
    sheet.define(
        Function("total", [n]),
        Program(local(acc, 0), For(i, Range(1, n), local(acc, acc + i)), acc),
        height=95,
    )
    sheet.evaluate(Symbol("total")(5), tag="for-15")
    sheet.define(
        Function("countdown", [n]),
        Program(local(acc, 0), While(n > 0, Program(local(acc, acc + n), local(n, n - 1))), acc),
        height=110,
    )
    sheet.evaluate(Symbol("countdown")(5), tag="while-15")
    sheet.define(Function("early", [n]), Program(If(n > 0, Return(7)), -1), height=65)
    sheet.evaluate(Symbol("early")(2), tag="return-7")
    sheet.define(
        Function("stop", [n]),
        Program(
            local(acc, 0),
            For(i, Range(1, n), Program(If(i > 3, Break()), local(acc, acc + i))),
            acc,
        ),
        height=115,
    )
    sheet.evaluate(Symbol("stop")(8), tag="break-6")
    sheet.define(
        Function("skip", [n]),
        Program(
            local(acc, 0),
            For(i, Range(1, n), Program(If(i.eq(3), Continue()), local(acc, acc + i))),
            acc,
        ),
        height=115,
    )
    sheet.evaluate(Symbol("skip")(5), tag="continue-12")
    sheet.define(Function("safe_inverse", [x]), Program(TryCatch(1 / x, 99), 0), height=65)
    # In Mathcad a program's last executed statement is its result.
    sheet.define(Function("safe", [x]), Program(local(acc, TryCatch(1 / x, 99)), acc), height=65)
    sheet.evaluate(Symbol("safe")(0), tag="catch-99")
    sheet.define(
        Function("piecewise", [x]),
        Program(If((x >= 0) & (x < 1), x), If(x >= 1, 2 * x), Otherwise(-x)),
        height=85,
    )
    sheet.evaluate(Symbol("piecewise")(2), tag="piecewise-4")
    sheet.math(Symbolic(x**2 - 1, commands=("factor",)), tag="factor", height=55)
    return sheet


if __name__ == "__main__":
    Path("output").mkdir(exist_ok=True)
    print(build().write("output/programs.xmcd"))
