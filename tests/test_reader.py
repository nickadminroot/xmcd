"""Editable roundtrips retain native content and invalidate dependent caches."""

from dataclasses import replace
from pathlib import Path

import pytest
from lxml import etree as ET

from xmcd import (
    Area,
    Define,
    MathRegion,
    Matrix,
    MatrixStyle,
    Number,
    NumberFormat,
    OpaqueExpression,
    OpaqueRegion,
    ResultFormat,
    Symbol,
    Trace,
    Worksheet,
    WorksheetValidationError,
)
from xmcd.document import NS
from xmcd.validation import ValidationError, parse_xml, validate

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.mark.parametrize("source", sorted(FIXTURES.glob("*.xmcd")), ids=lambda p: p.stem)
def test_native_roundtrip_without_edits_is_byte_identical(source):
    loaded = Worksheet.read(source)
    assert loaded.to_bytes() == source.read_bytes()


def test_edit_definition_clears_all_dependent_results_and_preserves_other_xml(tmp_path):
    source = FIXTURES / "core-mathcad14.xmcd"
    original = source.read_bytes()
    w = Worksheet.read(source)
    region = next(r for r in w.regions if r.tag == "input-a")
    assert isinstance(region.expression, Define)
    assert isinstance(region.expression.rhs, Number)
    region.expression = replace(region.expression, rhs=4)
    target = w.write(tmp_path / "edited.xmcd")
    root = parse_xml(target)
    assert not root.findall(".//ml:result", NS)
    assert root.xpath("//ws:region[@tag='input-a']//ml:real/text()", namespaces=NS) == ["4"]
    assert source.read_bytes() == original
    # Native rendering attributes on another expression survive the edit.
    assert root.xpath(
        "//ws:region[@tag='scalar-9']/ws:math/ml:eval/@placeholderMultiplicationStyle",
        namespaces=NS,
    ) == ["default"]
    region.expression = Define(Symbol("a"), 1 / Symbol("missing"))
    with pytest.raises(WorksheetValidationError):
        w.write(target)
    assert target.read_bytes() == ET.tostring(
        root, encoding="UTF-8", xml_declaration=True, pretty_print=True
    )


def test_edit_nested_expression_preserves_native_integral_attributes():
    w = Worksheet.read(FIXTURES / "core-mathcad14.xmcd")
    r = next(
        r
        for r in w.regions
        if isinstance(r, MathRegion)
        and r.expression.to_xml().find(".//ml:integral", NS) is not None
    )
    before = dict(w.to_xml().find(".//ml:integral", NS).attrib)
    r.expression = replace(r.expression, expression=r.expression.expression + 1)
    assert w.to_xml().find(".//ml:integral", NS).attrib == before


def test_matrix_column_order_greek_and_subscript_are_typed():
    from xmcd import Greek, LiteralSubscript

    w = Worksheet()
    a = Symbol(Greek.ALPHA, LiteralSubscript("q2"))
    w.define(a, Matrix([[1, 2, 3], [4, 5, 6]]))
    loaded = Worksheet.read(w.to_bytes())
    expression = loaded.regions[0].expression
    assert expression.lhs.name == a.name
    assert expression.lhs.subscript == a.subscript
    assert [[c.value for c in row] for row in expression.rhs.rows] == [[1, 2, 3], [4, 5, 6]]


def test_unknown_expression_and_graph_are_preserved_with_warning():
    w = Worksheet.read(FIXTURES / "plots-mathcad14.xmcd")
    graph = next(r for r in w.regions if isinstance(r, OpaqueRegion))
    assert graph.kind == "plot"
    root = w.to_xml()
    binaries = [n.text for n in root.findall("ws:binaryContent/ws:item", NS)]
    w.title = "Edited title"
    w.text("Additional note")
    assert [n.text for n in w.to_xml().findall("ws:binaryContent/ws:item", NS)] == binaries
    assert "opaque-region" in {d.code for d in w.check().warnings}
    with pytest.raises(WorksheetValidationError):
        w.validate(warnings_as_errors=True)
    w = Worksheet()
    w.math(
        OpaqueExpression(
            b'<ml:future xmlns:ml="http://schemas.mathsoft.com/math30" setting="preserve"/>'
        ),
        height=30,
    )
    loaded = Worksheet.read(w.to_bytes())
    assert isinstance(loaded.regions[0].expression, OpaqueExpression)
    assert loaded.to_bytes() == w.to_bytes()


def test_append_plot_allocates_new_ids_preserving_original_attachments():
    w = Worksheet.read(FIXTURES / "plots-mathcad14.xmcd")
    before = w.to_xml().findall("ws:binaryContent/ws:item", NS)
    t = Symbol("t")
    w.plot(Trace(t, t**2))
    root = w.to_xml()
    validate(ET.tostring(root))
    after = root.findall("ws:binaryContent/ws:item", NS)
    assert len(after) > len(before)
    assert [(n.get("item-id"), n.text) for n in after[: len(before)]] == [
        (n.get("item-id"), n.text) for n in before
    ]


def test_read_preserves_layout_until_explicit_reflow():
    from xmcd import Function, Range

    w = Worksheet()
    k, x = Symbol("k"), Symbol("x")
    g = Function(Symbol("g"), [x])
    w.define(g, x**2)
    w.define(k, Range(0, 10))
    w.evaluate(g(k), top=100, height=30, tag="table")
    w.text("After", top=140)
    loaded = Worksheet.read(w.to_bytes())
    assert loaded.regions[-2].height == 30
    loaded.reflow()
    table, text = loaded.regions[-2:]
    assert table.height > 360
    assert text.top >= table.top + table.height + 12
    first = loaded.to_bytes()
    assert loaded.to_bytes() == first


def test_settings_and_result_format_patch_only_changed_properties():
    w = Worksheet()
    w.evaluate(2, result_format=ResultFormat())
    root = w.to_xml()
    fmt = root.find(".//ws:math/ws:resultFormat", NS)
    fmt.set("show-trailing-zeros", "true")
    loaded = Worksheet.read(ET.tostring(root))
    loaded.origin = 1
    loaded.result_format = replace(loaded.result_format, notation=NumberFormat.DECIMAL)
    loaded.regions[0].result_format = ResultFormat(precision=4, matrix_style=MatrixStyle.TABLE)
    out = loaded.to_xml()
    assert out.find(".//ws:builtInVariables", NS).get("array-origin") == "1"
    assert out.find(".//ws:results/ws:decimal", NS) is not None
    assert out.find(".//ws:results/ws:general", NS) is None
    fmt = out.find(".//ws:math/ws:resultFormat", NS)
    assert fmt.get("show-trailing-zeros") == "true"
    assert fmt.find("ws:general", NS).get("precision") == "4"


def test_area_children_keep_identity_and_definition_scope():
    w = Worksheet()
    w.add(Area("Definitions", [MathRegion(Define(Symbol("a"), 2))]))
    w.evaluate(Symbol("a"))
    loaded = Worksheet.read(w.to_bytes())
    child = loaded.regions[0].regions[0]
    loaded.layout()
    assert loaded.regions[0].regions[0] is child
    child.expression = replace(child.expression, rhs=3)
    loaded.reflow()
    assert not loaded.check().errors
    root = loaded.to_xml()
    assert root.find(".//ws:area/ws:region/ws:math/ml:define/ml:real", NS).text == "3"
    assert loaded.to_bytes() == loaded.to_bytes()


def test_invalid_xml_is_rejected():
    with pytest.raises(ValidationError):
        Worksheet.read(b'<!DOCTYPE worksheet [<!ENTITY x "bad">]><worksheet/>')
    with pytest.raises(ValidationError):
        Worksheet.read(b"<worksheet>")


def test_edited_document_recalculated_in_native_mathcad():
    from xmcd.validation import calculation_errors

    source = FIXTURES / "reader-core-mathcad14.xmcd"
    root = parse_xml(source)
    assert not calculation_errors(source)
    assert root.xpath("//ws:region[@tag='scalar-9']//ml:result/ml:real/text()", namespaces=NS) == [
        "65"
    ]
    assert root.xpath(
        "//ws:region[@tag='function-12']//ml:result/ml:real/text()", namespaces=NS
    ) == ["12"]


def test_moving_nested_regions_and_changing_settings_invalidates_caches():
    source = FIXTURES / "advanced-mathcad14.xmcd"
    w = Worksheet.read(source)
    w.origin += 1
    assert not w.to_xml().findall(".//ml:result", NS)
    w = Worksheet.read(source)
    area = next(r for r in w.regions if isinstance(r, Area))
    area.regions.pop()
    assert not w.to_xml().findall(".//ml:result", NS)


def test_copied_expression_keeps_native_options_without_copying_cached_results():
    original = Worksheet.read(FIXTURES / "core-mathcad14.xmcd")
    expression = next(r.expression for r in original.regions if r.tag == "scalar-9")
    w = Worksheet()
    w.define(Symbol("a"), 4)
    w.math(expression)
    root = w.to_xml()
    assert not root.findall(".//ml:result", NS)
    assert root.find(".//ml:eval", NS).get("placeholderMultiplicationStyle") == "default"


def test_text_edit_preserves_paragraph_properties():
    w = Worksheet()
    w.text("Before")
    root = w.to_xml()
    root.find(".//ws:text/ws:p", NS).set("align", "center")
    loaded = Worksheet.read(ET.tostring(root))
    loaded.regions[0].text = "After"
    paragraph = loaded.to_xml().find(".//ws:text/ws:p", NS)
    assert paragraph.text == "After"
    assert paragraph.get("align") == "center"
