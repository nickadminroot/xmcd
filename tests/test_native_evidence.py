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
