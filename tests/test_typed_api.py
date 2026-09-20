"""The public API rejects ambiguous strings before XML serialization."""

import pytest

from xmcd import (
    BuiltinFunction,
    Call,
    Define,
    Function,
    LiteralSubscript,
    MathRegion,
    Matrix,
    Operator,
    PageSettings,
    Range,
    ResultFormat,
    Sequence,
    Solver,
    SolverKind,
    SolverMethod,
    String,
    Symbol,
    Symbolic,
    TextRegion,
    Trace,
    Worksheet,
    expr,
)


@pytest.mark.parametrize(
    "make",
    [
        lambda: expr("x"),
        lambda: Symbol("x") + "y",
        lambda: Symbol("x")["i"],
        lambda: Matrix([["x"]]),
        lambda: Define("x", 1),
        lambda: Define(Symbol("x"), "y"),
        lambda: Define(Symbol("x"), 1, kind="normal"),
        lambda: Function("g", [Symbol("x")]),
        lambda: Function(Symbol("g"), ["x"]),
        lambda: Call("sin", Symbol("x")),
        lambda: BuiltinFunction.SIN("x"),
        lambda: Range("a", 10),
        lambda: Operator("plus", 1, 2),
        lambda: Solver("Find"),
        lambda: Solver(SolverKind.FIND, method="linear"),
        lambda: Symbol("x", subscript="1"),
        lambda: Symbolic(Symbol("x"), commands=("factor",)),
        lambda: Symbolic(Symbol("x"), commands=(("collect", Symbol("x")),)),
        lambda: ResultFormat(notation="general"),
        lambda: ResultFormat(matrix_style="table"),
        lambda: TextRegion("Text", style="Normal"),
        lambda: PageSettings(orientation="portrait"),
        lambda: Trace("x", Symbol("y")),
        lambda: Trace(Symbol("x"), Symbol("y"), style="solid"),
        lambda: Trace(Symbol("x"), Symbol("y"), marker="none"),
        lambda: MathRegion("x"),
        lambda: Worksheet().evaluate("x"),
        lambda: Worksheet().evaluate(1, unit="m"),
    ],
)
def test_implicit_strings_are_rejected(make):
    with pytest.raises(TypeError):
        make()


def test_explicit_text_and_symbolic_commands_remain_supported():
    x = Symbol("x", subscript=LiteralSubscript("1"))
    assert String("text").to_xml().text == "text"
    command = Symbolic(x, commands=(Sequence(Symbol("collect"), x),)).to_xml()
    assert command[1][0][0].text == "collect"
    assert Solver(SolverKind.FIND, SolverMethod.LINEAR).to_xml().get("method") == "linear"
    with pytest.raises(ValueError, match="Unsupported method"):
        Solver(SolverKind.ODESOLVE, SolverMethod.LINEAR)
