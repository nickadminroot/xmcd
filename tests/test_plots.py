"""Graph archives must remain self-contained when composed or reused."""

import base64
from pathlib import Path

import pytest

from xmcd import Symbol, Trace, Worksheet, XYPlot, f, validate
from xmcd.document import NS


def test_graph_reuse_has_independent_binary_references():
    plot = XYPlot([Trace("t", f.sin("t")), Trace("t", f.cos("t"))])
    sheet = Worksheet()
    sheet.add(plot)
    sheet.add(plot)
    root = sheet.to_xml()
    assert [n.get("item-idref") for n in root.findall(".//ws:plot", NS)] == ["1", "2"]
    binaries = root.findall("ws:binaryContent/ws:item", NS)
    assert len(binaries) == 2
    assert binaries[0].text == binaries[1].text
    payload = base64.b64decode(binaries[0].text)
    assert b"d2_graph_format" in payload
    assert "sin".encode("utf-16le") in payload
    assert "cos".encode("utf-16le") in payload
    validate(sheet.to_bytes())


def test_native_plot_schema():
    schema = Path("research/schema/worksheet30.xsd")
    if not schema.exists():
        pytest.skip("Requires local PTC schemas")
    sheet = Worksheet()
    t = Symbol("t")
    sheet.plot(Trace(f.cos(t), f.sin(t)), x_bounds=(-1.2, 1.2), y_bounds=(-1.2, 1.2))
    validate(sheet.to_bytes(), schema=schema)


def test_invalid_plot_values_fail_before_serialization():
    with pytest.raises(ValueError, match="color"):
        Trace("x", "y", color="red")
    with pytest.raises(ValueError, match="Trace"):
        XYPlot([])
    with pytest.raises(ValueError, match="maximum"):
        XYPlot([Trace("x", "y")], x_bounds=(3, 1))
