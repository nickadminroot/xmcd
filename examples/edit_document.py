"""Load an XMCD document, edit a tagged definition and preserve its other content."""

from dataclasses import replace
from pathlib import Path

from xmcd import Define, MathRegion, Worksheet


def build():
    source = Path(__file__).resolve().parents[1] / "tests/fixtures/core-mathcad14.xmcd"
    w = Worksheet.read(source)
    region = next(r for r in w.regions if r.tag == "input-a")
    if not isinstance(region, MathRegion) or not isinstance(region.expression, Define):
        raise TypeError("input-a must be a definition")
    region.expression = replace(region.expression, rhs=4)
    w.text("Параметр изменён через объектную модель Python")
    w.reflow()
    return w


if __name__ == "__main__":
    Path("output").mkdir(exist_ok=True)
    print(build().write("output/edit_document.xmcd"))
