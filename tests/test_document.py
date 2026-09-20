import pytest
from lxml import etree as ET

from xmcd.document import NS, Area, PageSettings, ResultFormat, TextRegion, Worksheet
from xmcd.validation import ValidationError, validate


def test_nested_and_reused_regions_have_unique_ids():
    shared = TextRegion("One & <two>")
    sheet = Worksheet("Unicode: α, Русский")
    sheet.add(shared)
    sheet.add(Area("Details", [shared, shared], top=100))
    data = sheet.to_bytes()
    validate(data)
    root = ET.fromstring(data)
    ids = root.xpath("//ws:region/@region-id", namespaces=NS)
    assert len(set(ids)) == 4
    assert root.xpath("//ws:p/text()", namespaces=NS) == ["One & <two>"] * 3
    assert data == sheet.to_bytes()


def test_flow_advances_below_explicit_regions():
    sheet = Worksheet()
    sheet.add(TextRegion("Manual", top=200, height=80))
    next_region = sheet.text("Automatic")
    assert next_region.top >= 280


@pytest.mark.parametrize("value", [-1, float("nan"), float("inf")])
def test_invalid_geometry_rejected(value):
    with pytest.raises(ValueError):
        TextRegion("x", top=value)
    with pytest.raises(ValueError):
        PageSettings(margin_left=value)


def test_validation_rejects_missing_binary():
    sheet = Worksheet()
    root = sheet.to_xml()
    ET.SubElement(
        root.find("ws:regions", NS),
        f"{{{NS['ws']}}}region",
        attrib={"region-id": "1", "item-idref": "42"},
    )
    with pytest.raises(ValidationError, match="Dangling"):
        validate(ET.tostring(root))


def test_validation_rejects_dtd():
    with pytest.raises(ValidationError, match="DTD"):
        validate(b'<!DOCTYPE worksheet [<!ENTITY a "b">]><worksheet/>')


def test_formats_and_settings_reject_invalid_values():
    with pytest.raises(ValueError):
        ResultFormat(notation="float")
    with pytest.raises(ValueError):
        Worksheet(tolerance=2)


def test_native_schema_when_available():
    from pathlib import Path

    schema = Path("research/schema/worksheet30.xsd")
    if not schema.exists():
        pytest.skip("PTC schemas are local verification assets, not redistributed")
    sheet = Worksheet()
    sheet.text("Independent worksheet")
    sheet.add(Area("Nested", [TextRegion("Text")], top=80))
    validate(sheet.to_bytes(), schema=schema)
