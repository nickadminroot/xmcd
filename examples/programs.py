"""Local assignment, loops, branching, exceptions and symbolic evaluation."""

from pathlib import Path

from xmcd import (
    Break,
    Continue,
    Define,
    DefinitionKind,
    For,
    Function,
    If,
    Otherwise,
    Program,
    Range,
    ResultShape,
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
        return Define(a, b, kind=DefinitionKind.LOCAL)

    sheet.text("Native Mathcad programming operators", top=20)
    sheet.define(
        Function(Symbol("total"), [n]),
        Program(local(acc, 0), For(i, Range(1, n), local(acc, acc + i)), acc),
        height=95,
    )
    sheet.evaluate(Symbol("total")(5), result_shape=ResultShape.scalar(), tag="for-15")
    sheet.define(
        Function(Symbol("countdown"), [n]),
        Program(local(acc, 0), While(n > 0, Program(local(acc, acc + n), local(n, n - 1))), acc),
        height=110,
    )
    sheet.evaluate(Symbol("countdown")(5), result_shape=ResultShape.scalar(), tag="while-15")
    sheet.define(Function(Symbol("early"), [n]), Program(If(n > 0, Return(7)), -1), height=65)
    sheet.evaluate(Symbol("early")(2), result_shape=ResultShape.scalar(), tag="return-7")
    sheet.define(
        Function(Symbol("stop"), [n]),
        Program(
            local(acc, 0),
            For(i, Range(1, n), Program(If(i > 3, Break()), local(acc, acc + i))),
            acc,
        ),
        height=115,
    )
    sheet.evaluate(Symbol("stop")(8), result_shape=ResultShape.scalar(), tag="break-6")
    sheet.define(
        Function(Symbol("skip"), [n]),
        Program(
            local(acc, 0),
            For(i, Range(1, n), Program(If(i.eq(3), Continue()), local(acc, acc + i))),
            acc,
        ),
        height=115,
    )
    sheet.evaluate(Symbol("skip")(5), result_shape=ResultShape.scalar(), tag="continue-12")
    sheet.define(Function(Symbol("safe_inverse"), [x]), Program(TryCatch(1 / x, 99), 0), height=65)
    # In Mathcad a program's last executed statement is its result.
    sheet.define(
        Function(Symbol("safe"), [x]), Program(local(acc, TryCatch(1 / x, 99)), acc), height=65
    )
    sheet.evaluate(Symbol("safe")(0), result_shape=ResultShape.scalar(), tag="catch-99")
    sheet.define(
        Function(Symbol("piecewise"), [x]),
        Program(If((x >= 0) & (x < 1), x), If(x >= 1, 2 * x), Otherwise(-x)),
        height=85,
    )
    sheet.evaluate(Symbol("piecewise")(2), result_shape=ResultShape.scalar(), tag="piecewise-4")
    sheet.math(Symbolic(x**2 - 1, commands=(Symbol("factor"),)), tag="factor", height=55)
    return sheet


if __name__ == "__main__":
    Path("output").mkdir(exist_ok=True)
    print(build().write("output/programs.xmcd"))
