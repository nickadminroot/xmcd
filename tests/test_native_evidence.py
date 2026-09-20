"""Regression evidence from a real Mathcad UI recalculate / Save As operation."""

import math
from pathlib import Path

from xmcd.document import NS
from xmcd.validation import calculation_errors, parse_xml, validate


def test_native_core_has_every_expected_numeric_result():
    path = Path(__file__).parent / "fixtures/core-mathcad14.xmcd"
    validate(path)
    assert calculation_errors(path) == []
    root = parse_xml(path)
    expected = {
        "scalar-9": 9,
        "index-2": 2,
        "det-minus2": -2,
        "function-12": 12,
        "derivative-14": 14,
        "integral-third": 1 / 3,
        "sum-15": 15,
        "program-3": 3,
        "vector-9": 9,
    }
    actual = {}
    for region in root.findall("ws:regions/ws:region", NS):
        tag = region.get("tag")
        if tag in expected:
            value = region.find("ws:math/ml:eval/ml:result/ml:real", NS)
            assert value is not None, f"No saved result for {tag}"
            actual[tag] = float(value.text)
    assert actual.keys() == expected.keys()
    assert all(
        math.isclose(actual[k], v, rel_tol=1e-10, abs_tol=1e-10) for k, v in expected.items()
    )


def test_native_solve_blocks_have_saved_solutions():
    path = Path(__file__).parent / "fixtures/solvers-mathcad14.xmcd"
    validate(path)
    assert calculation_errors(path) == []
    root = parse_xml(path)
    vector = root.xpath(
        "//ws:region[@tag='solution-3-2']//ml:result/ml:matrix/ml:real", namespaces=NS
    )
    scalar = root.xpath("//ws:region[@tag='parameterized-3']//ml:result/ml:real", namespaces=NS)
    assert [float(n.text) for n in vector] == [3, 2]
    assert [float(n.text) for n in scalar] == [3]


def test_native_numerical_functions_and_table():
    path = Path(__file__).parent / "fixtures/numerics-mathcad14.xmcd"
    validate(path)
    assert calculation_errors(path) == []
    root = parse_xml(path)
    expected = {
        "linear-2.5": [2.5],
        "lspline-knot-1": [1],
        "pspline-knot-1": [1],
        "cspline-knot-1": [1],
        "linear-system-1-3": [1, 3],
        "augment-4": [4],
        "stack-4": [4],
        "vectorized-9": [9],
        "transpose-1": [1],
        "column-3": [3],
        "implicit-array-4": [4],
        "root-sqrt2": [math.sqrt(2)],
        "angle-90": [90],
        "rkfixed-e": [math.e],
        "Rkadapt-e": [math.e],
        "units-meter": [1],
    }
    for tag, values in expected.items():
        nodes = root.xpath("//ws:region[@tag=$tag]//ml:result//ml:real", tag=tag, namespaces=NS)
        actual = [float(n.text) for n in nodes]
        assert len(actual) == len(values), tag
        assert all(
            math.isclose(a, b, rel_tol=1e-6, abs_tol=1e-8) for a, b in zip(actual, values)
        ), tag
    table = root.xpath('//ws:region[@tag="ode-result-table"]', namespaces=NS)[0]
    result = table.find(".//ml:result/ml:matrix", NS)
    assert result is not None and result.get("rows") == "21" and result.get("cols") == "2"
    preceding = root.xpath('//ws:region[@tag="Rkadapt-e"]', namespaces=NS)[0]
    following = root.xpath('//ws:region[@tag="units-meter"]', namespaces=NS)[0]
    assert float(table.get("top")) > float(preceding.get("top")) + float(preceding.get("height"))
    assert float(following.get("top")) > float(table.get("top")) + float(table.get("height"))


def test_native_programming_and_symbolic_factorization():
    path = Path(__file__).parent / "fixtures/programs-mathcad14.xmcd"
    validate(path)
    assert calculation_errors(path) == []
    root = parse_xml(path)
    for tag, value in {
        "for-15": 15,
        "while-15": 15,
        "return-7": 7,
        "break-6": 6,
        "continue-12": 12,
        "catch-99": 99,
        "piecewise-4": 4,
    }.items():
        actual = root.xpath("//ws:region[@tag=$tag]//ml:result/ml:real", tag=tag, namespaces=NS)
        assert [float(n.text) for n in actual] == [value]
    result = root.find(".//ml:symResult/ml:apply", NS)
    assert result is not None and result[0].tag.endswith("mult")
    assert result.find(".//ml:minus", NS) is not None
    assert result.find(".//ml:plus", NS) is not None
    assert [n.text for n in result.findall(".//ml:id", NS)] == ["x", "x"]
