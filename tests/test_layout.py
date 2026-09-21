"""Conservative layout contracts; real rendering is tested by saved native fixtures."""

from itertools import pairwise

import pytest

from xmcd import (
    BuiltinFunction as B,
)
from xmcd import (
    Greek,
    LayoutError,
    LiteralSubscript,
    MathRegion,
    Matrix,
    MatrixStyle,
    Number,
    ResultFormat,
    ResultShape,
    Symbol,
    Trace,
    Worksheet,
)
from xmcd.document import NS


def test_nested_fractions_and_matrix_cells_expand_flow():
    x = Symbol("x")
    w = Worksheet()
    a = w.math(x / (1 + 1 / (x + 2)))
    b = w.math(Matrix([[x / (1 + 1 / x)], [x**3], [2]]))
    c = w.text("Next")
    assert a.height > 50
    assert b.height > a.height
    assert b.top >= a.top + a.height + 12
    assert c.top >= b.top + b.height + 12
    assert a.top < a.top + a._axis < a.top + a.height


def test_wrapping_and_font_size_are_conservative():
    def height(size, width):
        return Worksheet(font_size=size).text("Wide text " * 40, width=width).height

    assert height(14, 200) > height(10, 200)
    assert height(10, 100) > height(10, 200)


def test_inferred_matrix_and_table_results_reserve_rows():
    w = Worksheet()
    a = Symbol("A")
    w.define(a, Matrix([[1, 2]] * 12))
    matrix = w.evaluate(a)
    table = w.evaluate(a, result_format=ResultFormat(matrix_style=MatrixStyle.TABLE))
    assert table.height > matrix.height > 200
    assert table.top >= matrix.top + matrix.height + 12


def test_opaque_result_requires_dimensions_instead_of_silent_scalar_guess():
    w = Worksheet()
    w.evaluate(Symbol("custom")(1))
    with pytest.raises(LayoutError, match="result_shape"):
        w.to_bytes()
    w.regions[0].result_shape = ResultShape(20, 3)
    w.to_bytes()
    assert w.regions[0].height > 350


def test_reflow_and_reuse_do_not_move_other_occurrences():
    source = MathRegion(Number(2))
    w = Worksheet(regions=[source, source])
    assert w.regions[0] is not w.regions[1]
    assert source.height is None and source.top is None
    old_top = w.regions[1].top
    w.regions[0].expression = Matrix.vector(range(15))
    w.to_bytes()
    assert w.regions[1].top > old_top + 200


def test_explicit_positions_and_heights_remain_explicit():
    w = Worksheet()
    region = w.add(MathRegion(Number(2), top=100, height=80))
    next_region = w.math(Number(3))
    assert region.top == 100 and region.height == 80
    assert next_region.top >= 192


def test_global_definition_and_indexed_array_dimensions():
    from xmcd import Define, DefinitionKind

    w = Worksheet()
    a = Symbol("A")
    w.evaluate(a)
    w.math(Define(a, Matrix.vector(range(10)), kind=DefinitionKind.GLOBAL))
    w.to_bytes()
    assert w.regions[0].height > 180
    z = Symbol("Z")
    w.define(z[9, 2], 0)
    assert w.evaluate(z).height > 180


def test_graph_labels_reserve_space_and_have_automatic_height():
    t = Symbol("t")
    w = Worksheet()
    graph = w.plot(Trace(t / (1 + t), B.SIN(t)), width=360)
    following = w.text("After graph")
    assert graph.height >= 220
    assert following.top > graph.top + graph.height + 30


def test_greek_literal_and_array_subscripts_have_distinct_semantics():
    phi = Symbol(Greek.PHI, subscript=LiteralSubscript("12"))
    assert phi.to_xml().text == "φ"
    assert phi.to_xml().get("subscript") == "12"
    assert phi[2].to_xml()[0].tag.endswith("indexer")
    assert (
        Symbol(Greek.OMEGA, subscript=LiteralSubscript(Greek.THETA)).to_xml().get("subscript")
        == "θ"
    )
    assert B.SIN(phi).to_xml()[0].text == "sin"


def test_matrix_values_and_native_layout_fixtures():
    from pathlib import Path

    from xmcd.validation import calculation_errors, parse_xml

    for size in (10, 14):
        path = Path(__file__).parent / f"fixtures/layout-{size}-mathcad14.xmcd"
        root = parse_xml(path)
        assert calculation_errors(path) == []
        assert not root.xpath('//*[@show-highlight="true"]')
        regions = root.findall("ws:regions/ws:region", NS)
        for a, b in pairwise(regions):
            assert float(b.get("top")) >= float(a.get("top")) + float(a.get("height")) + 6, (
                size,
                a.get("tag"),
                b.get("tag"),
            )
        for tag, value in [
            ("greek-15", 15),
            ("nested-fraction", 0.90625),
            ("indexed-1", 1),
            ("integral-third", 1 / 3),
        ]:
            actual = root.xpath(
                "//ws:region[@tag=$tag]//ml:result/ml:real/text()", tag=tag, namespaces=NS
            )
            assert float(actual[0]) == pytest.approx(value)
        for tag in ("matrix-result", "result-table"):
            matrix = root.xpath(
                "//ws:region[@tag=$tag]//ml:result/ml:matrix", tag=tag, namespaces=NS
            )[0]
            assert (matrix.get("rows"), matrix.get("cols")) == ("8", "3")


def test_expression_nodes_store_typed_children():
    from xmcd import Define, DefinitionKind, Function, If, Integral, Range

    x = Symbol("x")
    definition = Define(x, 2, kind=DefinitionKind.NORMAL)
    assert isinstance(definition.rhs, Number)
    assert isinstance(If(x > 0, 3).value, Number)
    assert isinstance(Range(0, 10).stop, Number)
    assert isinstance(Integral(x, x, 0, 1).upper, Number)
    assert isinstance(Function(x, (Symbol(n) for n in ["a"])).parameters, tuple)
    with pytest.raises(ValueError):
        Function(x, iter(()))


def test_program_with_growing_array_requires_result_shape():
    from xmcd import Define, DefinitionKind, For, Function, Program, Range

    n, i, acc = Symbol("n"), Symbol("i"), Symbol("acc")
    g = Function(Symbol("grow"), [n])
    w = Worksheet()
    w.define(
        g,
        Program(
            Define(acc, Matrix.vector([0]), kind=DefinitionKind.LOCAL),
            For(i, Range(1, n), Define(acc, B.STACK(acc, acc), kind=DefinitionKind.LOCAL)),
            acc,
        ),
    )
    w.evaluate(g(4))
    with pytest.raises(LayoutError, match="result_shape"):
        w.to_bytes()
    w.regions[-1].result_shape = ResultShape(16, 1)
    w.to_bytes()
    assert w.regions[-1].height > 280


def test_range_results_reserve_table_rows_even_for_scalar_functions():
    from xmcd import Function, Range

    k, x = Symbol("k"), Symbol("x")
    g = Function(Symbol("g"), [x])
    for formula in (B.ANGLE(1, x), Number(7)):
        w = Worksheet()
        w.define(g, formula)
        w.define(k, Range(0, 40))
        result = w.evaluate(g(k))
        after = w.text("After table")
        assert result.height > 40 * 18
        assert result._axis == pytest.approx(result.height / 2)
        assert after.top >= result.top + result.height + 12


def test_unknown_range_length_and_explicit_table_have_conservative_minimum():
    from xmcd import Range

    k = Symbol("k")
    w = Worksheet()
    w.define(Symbol("stop"), Number(4).sqrt())
    w.define(k, Range(0, Symbol("stop"), second=0.1))
    result = w.evaluate(B.ANGLE(1, k))
    assert result.height > 20 * 18
    w = Worksheet(result_format=ResultFormat(matrix_style=MatrixStyle.TABLE, table_min_rows=30))
    result = w.evaluate(Symbol("external")(1))
    assert result.height > 30 * 18


def test_calculus_bound_ranges_do_not_create_spurious_tables():
    from xmcd import Integral, Range, Sum

    k = Symbol("k")
    w = Worksheet()
    w.define(k, Range(0, 40))
    assert w.evaluate(Sum(k, k, 1, 5)).height < 200
    assert w.evaluate(Integral(k, k, 0, 1)).height < 200
    assert w.evaluate(B.ROOT(k**2 - 2, k, 0, 2)).height < 200
    w.define(k, 2)
    assert w.evaluate(B.ANGLE(1, k)).height < 100


def test_table_min_rows_validation_and_matrix_style():
    for value in (0, -1, 1.5, True):
        with pytest.raises(ValueError, match="table_min_rows"):
            ResultFormat(table_min_rows=value)
    w = Worksheet()
    a = Symbol("A")
    w.define(a, Matrix.vector([1, 2]))
    matrix = w.evaluate(a)
    table = w.evaluate(a, result_format=ResultFormat(matrix_style=MatrixStyle.TABLE))
    assert matrix.height < 100
    assert table.height > 20 * 18


def test_range_tables_native_bounds_and_values():
    from pathlib import Path

    from xmcd.validation import calculation_errors, parse_xml

    for size in (10, 14):
        path = Path(__file__).parent / "fixtures" / f"range-tables-{size}-mathcad14.xmcd"
        root = parse_xml(path)
        assert not calculation_errors(path)
        regions = root.findall("ws:regions/ws:region", NS)
        for first, second in pairwise(regions):
            assert (
                float(second.get("top")) - float(first.get("top")) - float(first.get("height")) >= 6
            )
        matrices = root.findall(".//ml:result/ml:matrix", NS)
        assert len(matrices) == 5
        assert matrices[0].get("rows") == "21"
        values = matrices[0].findall("ml:real", NS)
        assert float(values[0].text) == pytest.approx(0)
        assert float(values[-1].text) == pytest.approx(4)
        assert {float(n.text) for n in matrices[1].findall("ml:real", NS)} == {7}
