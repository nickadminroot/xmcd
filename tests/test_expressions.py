from pathlib import Path

import pytest
from lxml import etree as ET

from xmcd import (
    BuiltinFunction,
    Call,
    Derivative,
    Function,
    If,
    Integral,
    LiteralSubscript,
    Matrix,
    Operator,
    OperatorKind,
    Otherwise,
    Program,
    Range,
    String,
    Sum,
    Symbol,
    Worksheet,
    validate,
)
from xmcd.document import NS


def test_nonsymmetric_matrix_is_serialized_by_columns():
    matrix = Matrix([[1, 2, 3], [4, 5, 6]]).to_xml()
    assert matrix.get("rows") == "2"
    assert matrix.get("cols") == "3"
    assert [v.text for v in matrix] == ["1", "4", "2", "5", "3", "6"]


def test_invalid_matrix_and_operator_fail_early():
    with pytest.raises(ValueError):
        Matrix([[1], [2, 3]])
    with pytest.raises(ValueError):
        Operator(OperatorKind.POWER, 2)
    with pytest.raises(TypeError):
        Operator("arbitrary", 1)


def test_reusing_expressions_does_not_move_children():
    x = Symbol("x")
    shared = BuiltinFunction.SIN(x) + 1
    original = ET.tostring(shared.to_xml())
    other = shared * shared
    assert len(other.to_xml()) == 3
    assert ET.tostring(shared.to_xml()) == original


def test_comparisons_cannot_silently_become_python_booleans():
    with pytest.raises(TypeError):
        bool(Symbol("x") < 3)


def test_symbol_subscript_is_distinct_from_array_index():
    x = Symbol("x", subscript=LiteralSubscript("A"))
    assert x.to_xml().get("subscript") == "A"
    assert x[2].to_xml()[0].tag.endswith("indexer")
    assert x[1, 2].to_xml()[2].tag.endswith("sequence")


def test_xml_escaping_and_open_function_namespace():
    assert ET.fromstring(ET.tostring(String("<a & b>").to_xml())).text == "<a & b>"
    call = Call(Symbol("user_function"), 1, Symbol("θ"))
    assert call.to_xml()[0].text == "user_function"
    assert call.to_xml()[1].tag.endswith("sequence")


def test_native_expression_schema():
    schema = Path("research/schema/worksheet30.xsd")
    if not schema.exists():
        pytest.skip("Requires local PTC schemas")
    x = Symbol("x")
    sheet = Worksheet()
    sheet.define(x, 2)
    sheet.define(Symbol("A"), Matrix([[1, 2], [3, 4]]))
    sheet.define(Symbol("i"), Range(0, 10, second=0.1))
    sheet.define(Function(Symbol("g"), [x]), Program(If(x > 0, x), Otherwise(-x)))
    for expression in (
        BuiltinFunction.SIN(x),
        Derivative(x**3, x),
        Integral(x**2, x, 0, 1),
        Sum(x, x, 1, 5),
    ):
        sheet.evaluate(expression)
    validate(sheet.to_bytes(), schema=schema)
    assert len(sheet.to_xml().findall("ws:regions/ws:region", NS)) == 8
