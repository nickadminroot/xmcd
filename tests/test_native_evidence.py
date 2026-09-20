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


def test_native_optimization_and_hodograph_magnitude():
    cases = {
        "optimization-mathcad14.xmcd": {"minimum-3": 3, "maximum-2": 2, "minerr-2": 2},
        "hodograph-mathcad14.xmcd": {"magnitude-at-1": math.sqrt(5 + 4 * math.cos(1))},
    }
    for filename, expected in cases.items():
        path = Path(__file__).parent / "fixtures" / filename
        validate(path)
        assert calculation_errors(path) == []
        root = parse_xml(path)
        for tag, expected_value in expected.items():
            result = root.xpath("//ws:region[@tag=$tag]//ml:result/ml:real", tag=tag, namespaces=NS)
            assert len(result) == 1
            assert math.isclose(float(result[0].text), expected_value, rel_tol=1e-6, abs_tol=1e-8)


def test_native_operator_grouping():
    path = Path(__file__).parent / "fixtures/precedence-mathcad14.xmcd"
    assert calculation_errors(path) == []
    root = parse_xml(path)
    expected = {
        "multiply-sum": [14],
        "sum-multiply": [20],
        "minus-sum": [-5],
        "minus-minus": [3],
        "negative-sum": [-5],
        "power-sum": [625],
        "power-power": [4096],
        "power-exponent": [128],
        "negative-base": [4],
        "negative-expression": [4],
        "factorial-sum": [120],
        "fraction-sum": [5 / 6],
        "nested-fraction": [8 / 3],
        "boolean": [1],
        "sqrt": [math.sqrt(5)],
        "transpose": [5, 5, 5, 5],
    }
    for tag, values in expected.items():
        actual = root.xpath(
            "//ws:region[@tag=$tag]//ml:result//ml:real/text()", tag=tag, namespaces=NS
        )
        assert len(actual) == len(values), tag
        assert all(math.isclose(float(a), b) for a, b in zip(actual, values)), tag


def test_native_compressor_kinematics_against_analytic_solution():
    path = Path(__file__).parent / "fixtures/compressor-mathcad14.xmcd"
    assert calculation_errors(path) == []
    root = parse_xml(path)
    phi, crank, rod = 2 * math.pi / 3, 0.08, 0.32
    s, c = math.sin(phi), math.cos(phi)
    u = rod**2 - crank**2 * s**2
    vy = -crank * s - crank**2 * s * c / math.sqrt(u)
    ay = -crank * c - crank**2 * math.cos(2 * phi) / math.sqrt(u) - crank**4 * (s * c) ** 2 / u**1.5
    vphi2 = crank * c / math.sqrt(u)
    vx_center = 0.67 * crank * c
    vy_center = -crank * s - 0.33 * crank**2 * s * c / math.sqrt(u)
    inertia = 0.22 * vphi2**2 + 8 * (vx_center**2 + vy_center**2) + 10 * vy**2
    expected = {
        "probe-yC": crank * c + math.sqrt(u),
        "probe-v_yC": vy,
        "probe-a_yC": ay,
        "probe-v_phi2": vphi2,
        "inertia-at-probe": inertia,
        "probe-moment": -80 * vy_center - 100 * vy,
    }
    for tag, value in expected.items():
        actual = root.xpath(
            "//ws:region[@tag=$tag]//ml:result/ml:real/text()", tag=tag, namespaces=NS
        )
        assert len(actual) == 1
        assert math.isclose(float(actual[0]), value, rel_tol=1e-9, abs_tol=1e-10), tag
    table = root.xpath('//ws:region[@tag="mechanism-table"]//ml:result/ml:matrix', namespaces=NS)[0]
    assert (table.get("rows"), table.get("cols")) == ("13", "5")


def test_native_roundtrip_preserves_generated_expression_trees():
    """No equation-auditor rewrites, even when they leave no calculation error."""
    import runpy

    def shape(node):
        # Ignore presentation attributes and computed results, preserve operand order.
        if (
            node.tag.endswith("}apply")
            and len(node) == 2
            and node[0].tag.endswith("}neg")
            and node[1].tag.endswith("}real")
        ):
            return node[1].tag, str(-float(node[1].text)), ()
        if node.tag.endswith("}real"):
            return node.tag, str(float(node.text)), ()
        return node.tag, (node.text or "").strip(), tuple(shape(child) for child in node)

    for name in ("precedence", "compressor", "cam"):
        source = runpy.run_path(str(Path(__file__).parents[1] / "examples" / f"{name}.py"))[
            "build"
        ]().to_xml()
        saved = parse_xml(Path(__file__).parent / f"fixtures/{name}-mathcad14.xmcd")
        source_math = source.findall("ws:regions/ws:region/ws:math", NS)
        saved_math = saved.findall("ws:regions/ws:region/ws:math", NS)
        assert len(source_math) == len(saved_math)
        for before, after in zip(source_math, saved_math):
            a, b = before[0], after[0]
            if a.tag.endswith("}eval"):
                a, b = a[0], b[0]
            assert shape(a) == shape(b), before.getparent().get("region-id")
    for path in (Path(__file__).parent / "fixtures").glob("*.xmcd"):
        assert not parse_xml(path).xpath('//ws:region[@show-highlight="true"]', namespaces=NS), path


def test_native_ui_parameter_edit_recalculates_connected_document():
    before = parse_xml(Path(__file__).parent / "fixtures/compressor-mathcad14.xmcd")
    path = Path(__file__).parent / "fixtures/compressor-edited-mathcad14.xmcd"
    after = parse_xml(path)
    assert calculation_errors(path) == []
    n1 = after.xpath('//ml:define[ml:id="n1"]/ml:real/text()', namespaces=NS)
    assert n1 == ["20"]
    for tag in ("crank-0.08", "rod-0.32", "probe-yC", "probe-v_yC", "cycle-work"):
        values = [
            float(
                root.xpath(
                    "//ws:region[@tag=$tag]//ml:result/ml:real/text()", tag=tag, namespaces=NS
                )[0]
            )
            for root in (before, after)
        ]
        assert math.isclose(values[1], values[0] / 2, rel_tol=1e-9), tag


def test_native_cam_synthesis_and_complete_graphs():
    path = Path(__file__).parent / "fixtures/cam-mathcad14.xmcd"
    assert calculation_errors(path) == []
    root = parse_xml(path)

    def scalar(tag):
        return float(
            root.xpath("//ws:region[@tag=$tag]//ml:result/ml:real/text()", tag=tag, namespaces=NS)[
                0
            ]
        )

    assert math.isclose(scalar("normalized-lift"), 0.015, abs_tol=1e-8)
    assert abs(scalar("normalized-closure")) < 1e-6
    assert math.isclose(scalar("pressure-plus30"), 30, abs_tol=1e-8)
    assert math.isclose(scalar("pressure-minus30"), -30, abs_tol=1e-8)
    assert math.isclose(
        scalar("cam-r0"), math.hypot(scalar("cam-s0"), scalar("cam-e")), abs_tol=1e-10
    )
    assert root.xpath("//ws:region[ws:plot]/@tag", namespaces=NS) == [
        "cam-a",
        "cam-v",
        "cam-s",
        "cam-phase-portrait",
        "cam-pressure-angle",
        "cam-profile",
    ]


def test_native_large_graph_and_long_name_survive_save():
    path = Path(__file__).parent / "fixtures/graph-stress-mathcad14.xmcd"
    assert calculation_errors(path) == []
    root = parse_xml(path)
    assert root.xpath("//ws:region[ws:plot]/@tag", namespaces=NS) == [
        "style-probe",
        "name-70",
        "tree-over-255",
    ]


def test_native_plot_expressions_and_point_markers():
    path = Path(__file__).parent / "fixtures/plot-expressions-mathcad14.xmcd"
    assert calculation_errors(path) == []
    root = parse_xml(path)
    assert root.xpath("//ws:region[ws:plot]/@tag", namespaces=NS) == [
        "compound-operators",
        "point-markers",
    ]


def test_native_advanced_operators_and_retained_area_definitions():
    path = Path(__file__).parent / "fixtures/advanced-mathcad14.xmcd"
    assert calculation_errors(path) == []
    root = parse_xml(path)
    expected = {
        "area-value-7": [7],
        "hidden-value-13": [13],
        "global-before-definition-11": [11],
        "row-1-2": [1, 2],
        "cross-0-0-1": [0, 0, 1],
        "vector-sum-6": [6],
        "product-120": [120],
        "factorial-120": [120],
        "fifth-root-2": [2],
        "base2-log-3": [3],
        "abs-5": [5],
        "string-length-7": [7],
        "odesolve-e": [math.e],
    }
    for tag, values in expected.items():
        actual = root.xpath(
            "//ws:region[@tag=$tag]//ml:result//ml:real/text()", tag=tag, namespaces=NS
        )
        assert len(actual) == len(values), tag
        assert all(
            math.isclose(float(a), b, rel_tol=2e-6, abs_tol=1e-10) for a, b in zip(actual, values)
        ), tag
    assert root.xpath(
        '//ws:area[@is-collapsed="true"]//ml:define[ml:id="hidden"]/ml:real/text()', namespaces=NS
    ) == ["13"]
    assert root.xpath(
        '//ws:area[@is-collapsed="false"]//ml:define[ml:id="a"]/ml:real/text()', namespaces=NS
    ) == ["5"]
    assert len(root.findall(".//ws:pageBreak", NS)) == 1
    assert root.xpath(
        '//ws:region[@tag="complex-2-minus3i"]//ml:complex/ml:imag/text()', namespaces=NS
    ) == ["-3"]
