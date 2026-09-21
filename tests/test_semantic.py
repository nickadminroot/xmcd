"""Semantic acceptance covers invalid inputs and matching valid counterexamples."""

import runpy
from pathlib import Path

import pytest

from xmcd import (
    Area,
    Break,
    Define,
    DefinitionKind,
    Function,
    Given,
    If,
    Integral,
    LiteralSubscript,
    MathRegion,
    Matrix,
    Number,
    Otherwise,
    Placeholder,
    Program,
    Range,
    ResultShape,
    Solver,
    Symbol,
    Symbolic,
    ValidationContext,
    Worksheet,
    WorksheetValidationError,
)
from xmcd import (
    BuiltinFunction as B,
)


def sheet_with(expression):
    w = Worksheet()
    w.math(expression, height=80, tag="probe")
    return w


def codes(w):
    return {d.code for d in w.check().errors}


@pytest.mark.parametrize(
    ("expression", "code"),
    [
        (Symbol("missing") + 1, "undefined-symbol"),
        (Symbol("sni")(1), "undefined-function"),
        (B.SIN(1, 2), "function-arity"),
        (Define(Number(1) + 2, 3), "assignment-target"),
        (Define(Symbol("x"), 1, kind=DefinitionKind.LOCAL), "program-context"),
        (Break(), "loop-context"),
        (If(Number(1).eq(1), 3), "program-context"),
        (Placeholder(), "placeholder"),
        (Number(1) / 0, "division-by-zero"),
        (Range(1, 5, second=1), "range-step"),
        (Number(2).nth_root(0), "root-degree"),
        (Number(8).log(1), "log-base"),
        (Matrix([[1, 2, 3], [4, 5, 6]]) * Matrix([[1, 2], [3, 4]]), "matrix-dimensions"),
        (Matrix([[1, 2]]) + Matrix([[1], [2]]), "matrix-dimensions"),
        (Matrix([[1, 2]]).determinant(), "matrix-dimensions"),
        (Matrix([[1, 2], [3, 4]])[2, 0], "index-bounds"),
        (Matrix([[1, 2], [3, 4]])[0, -1], "index-domain"),
        (Matrix([[1, 2], [3, 4]])[0, 0.5], "index-domain"),
        (Matrix([[1, 2]]).column(2), "index-bounds"),
        (Number(1)[0], "matrix-required"),
        (B.AUGMENT(Matrix([[1]]), Matrix([[2], [3]])), "matrix-dimensions"),
        (B.STACK(Matrix([[1]]), Matrix([[2, 3]])), "matrix-dimensions"),
        (B.LSOLVE(Matrix([[1, 2]]), Matrix([[1]])), "matrix-dimensions"),
        (Symbol("m") + Symbol("s"), "unit-mismatch"),
        (B.SIN(2 * Symbol("m")), "unit-mismatch"),
        (Matrix([[Symbol("m"), Symbol("s")]]), "unit-mismatch"),
        (Solver()(Symbol("x")), "solve-block"),
        (Given(), "solve-block"),
    ],
)
def test_invalid_expressions_are_diagnosed(expression, code):
    assert code in codes(sheet_with(expression))


def test_write_preserves_existing_file_and_exposes_context(tmp_path):
    destination = tmp_path / "important.xmcd"
    destination.write_text("original")
    w = sheet_with(Symbol("missing"))
    with pytest.raises(WorksheetValidationError) as exc:
        w.write(destination)
    assert destination.read_text() == "original"
    diagnostic = exc.value.report.errors[0]
    assert diagnostic.region == 1 and diagnostic.tag == "probe"
    assert diagnostic.path == "expression"
    assert "missing" in str(exc.value)


def test_spatial_order_globals_and_disabled_definitions():
    x = Symbol("x")
    w = Worksheet()
    w.define(x, 1, top=200)
    w.evaluate(x, top=20, height=30)
    assert "undefined-symbol" in codes(w)
    w = Worksheet()
    w.evaluate(x, top=20, height=30)
    w.math(Define(x, 1, kind=DefinitionKind.GLOBAL), top=200)
    assert not w.check().errors
    w.regions[1].disabled = True
    assert "undefined-symbol" in codes(w)


def test_global_definitions_follow_their_own_order():
    x, y = Symbol("x"), Symbol("y")
    w = Worksheet()
    w.math(Define(x, y, kind=DefinitionKind.GLOBAL))
    w.math(Define(y, 2, kind=DefinitionKind.GLOBAL))
    assert "undefined-symbol" in codes(w)


def test_function_scope_arity_calls_and_captured_values():
    x = Symbol("x")
    g = Function(Symbol("g"), [x])
    w = Worksheet()
    w.define(g, x + 1)
    assert not w.check().errors
    w.evaluate(g(1, 2), height=30)
    assert "function-arity" in codes(w)
    w = Worksheet()
    w.define(g, 1 / x)
    w.evaluate(g(0), height=30)
    assert "division-by-zero" in codes(w)
    w = Worksheet()
    a = Symbol("a")
    w.define(a, 2)
    w.define(g, a / x)
    w.define(a, 0)
    w.evaluate(g(1), height=30)
    assert not w.check().errors


def test_not_callable_duplicate_parameters_and_literal_index_identity():
    x = Symbol("x")
    w = Worksheet()
    w.define(x, 1)
    w.evaluate(x(2), height=30)
    assert "not-callable" in codes(w)
    assert "duplicate-parameter" in codes(sheet_with(Define(Function(Symbol("g"), [x, x]), x)))
    w = Worksheet()
    w.define(x, 1)
    w.evaluate(Symbol("x", LiteralSubscript("1")), height=30)
    assert "undefined-symbol" in codes(w)


def test_program_locals_do_not_leak_and_calculus_binds_variable():
    x = Symbol("x")
    w = Worksheet()
    w.define(Symbol("p"), Program(Define(x, 2, kind=DefinitionKind.LOCAL), x))
    w.evaluate(x, height=30)
    assert "undefined-symbol" in codes(w)
    w = sheet_with(Integral(x**2, x, 0, 1))
    assert not w.check().errors
    assert w.check().warnings
    with pytest.raises(WorksheetValidationError):
        w.validate(warnings_as_errors=True)


def test_symbolic_free_variables_are_valid_and_reported_unchecked():
    w = sheet_with(Symbolic(Symbol("x") ** 2, commands=(Symbol("factor"),)))
    assert not w.check().errors
    assert any(d.code == "symbolic-unchecked" for d in w.check().warnings)


def test_origins_range_assignment_and_matrix_vector_operations():
    a, i = Symbol("a"), Symbol("i")
    w = Worksheet(origin=1)
    w.define(i, Range(1, 5))
    w.define(a[i], i**2)
    w.evaluate(a[5], height=30)
    assert not w.check().errors
    w.evaluate(a[6], height=30)
    assert "index-bounds" in codes(w)
    v = Matrix.vector([1, 2, 3])
    assert not sheet_with(v * v).check().errors
    assert not sheet_with((v * v).vectorize()).check().errors


def test_units_allow_conversion_and_dimension_cancellation():
    m, s = Symbol("m"), Symbol("s")
    for expression in ((m**2).sqrt() + m, m / s * s + m, Matrix([[0, m]])):
        assert not sheet_with(expression).check().errors
    w = Worksheet()
    w.evaluate(1000 * Symbol("mm"), unit=m, height=40)
    assert not w.check().errors
    w.evaluate(m, unit=s, height=40)
    assert "unit-mismatch" in codes(w)


def test_external_functions_are_explicit_and_unverified():
    g = Function(Symbol("extension_fn"), [Symbol("x")])
    w = Worksheet()
    w.evaluate(g(1), result_shape=ResultShape.scalar())
    assert "undefined-function" in codes(w)
    report = w.validate(context=ValidationContext(functions=(g,)))
    assert not report.errors
    assert any(d.code == "external-unchecked" for d in report.warnings)


def test_area_definitions_are_visible():
    x = Symbol("x")
    w = Worksheet()
    w.add(Area("Definitions", [MathRegion(Define(x, 2))], collapsed=True))
    w.evaluate(x)
    assert not w.check().errors


@pytest.mark.parametrize("name", [p.stem for p in sorted(Path("examples").glob("*.py"))])
def test_all_existing_examples_pass_semantic_validation_and_write(name, tmp_path):
    w = runpy.run_path(f"examples/{name}.py")["build"]()
    report = w.validate()
    assert not report.errors
    w.write(tmp_path / f"{name}.xmcd")


def test_conditional_program_does_not_turn_possible_values_into_proven_zero():
    x, acc = Symbol("x"), Symbol("acc")
    g = Function(Symbol("g"), [x])
    w = Worksheet()
    w.define(g, Program(If(x > 0, 1), Otherwise(0)))
    w.evaluate(1 / g(1), height=40)
    assert not w.check().errors
    w = Worksheet()
    w.define(
        g,
        Program(
            Define(acc, 0, kind=DefinitionKind.LOCAL),
            If(x > 0, Define(acc, 1, kind=DefinitionKind.LOCAL)),
            1 / acc,
        ),
    )
    w.evaluate(g(1), height=40)
    assert not w.check().errors


def test_numeric_derivative_and_two_argument_root_need_evaluation_points():
    from xmcd import Derivative

    x = Symbol("x")
    assert "undefined-symbol" in codes(sheet_with(Derivative(x**2, x)))
    assert "undefined-symbol" in codes(sheet_with(B.ROOT(x**2 - 2, x)))
    assert not sheet_with(B.ROOT(x**2 - 2, x, 0, 2)).check().errors


def test_native_mathcad_confirms_rejected_cases_and_valid_counterexamples():
    from xmcd import calculation_errors
    from xmcd.document import NS
    from xmcd.validation import parse_xml

    w = runpy.run_path("tests/validation_cases.py")["build"]()
    path = Path("tests/fixtures/validation/errors-mathcad14.xmcd")
    native = {e.tag for e in calculation_errors(path)}
    static = {e.tag for e in w.check().errors}
    assert (
        native
        == static
        == {
            "undefined-symbol",
            "function-arity",
            "matrix-dimensions",
            "index-bounds",
            "unit-mismatch",
            "division-by-zero",
            "factorial-probe",
        }
    )
    root = parse_xml(path)
    for tag, expected in [("valid-dot-14", 14), ("valid-minimum-3", 3)]:
        results = root.xpath(
            "//ws:region[@tag=$tag]//ml:result/ml:real/text()", tag=tag, namespaces=NS
        )
        assert float(results[0]) == pytest.approx(expected)


def test_mutated_geometry_and_literal_callees_are_rejected(tmp_path):
    w = Worksheet()
    w.text("x").height = -1
    assert "region-geometry" in codes(w)
    with pytest.raises(WorksheetValidationError):
        w.write(tmp_path / "bad.xmcd")
    assert "not-callable" in codes(sheet_with(Number(1)(2)))


def test_origin_constant_and_caught_builtin_error():
    from xmcd import TryCatch

    w = Worksheet(origin=1)
    a = Symbol("a")
    w.define(a, Matrix.vector([1, 2]))
    w.evaluate(a[Symbol("ORIGIN")])
    assert not w.check().errors
    program = Program(TryCatch(B.LSOLVE(Matrix([[1, 2]]), Matrix([[1]])), 99), 0)
    assert not sheet_with(program).check().errors


def test_repeated_function_graph_is_memoized_without_losing_errors(monkeypatch):
    from xmcd import Define, Function, Symbol, Worksheet
    from xmcd.semantic import _Analyzer

    x = Symbol("x")
    w = Worksheet()
    previous = Function(Symbol("f0"), [x])
    w.math(Define(previous, 1 / x))
    for i in range(1, 16):
        current = Function(Symbol(f"f{i}"), [x])
        w.math(Define(current, previous(x) + previous(x)))
        previous = current
    w.evaluate(previous(1), height=30, tag="valid")
    w.evaluate(previous(0), height=30, tag="invalid1")
    w.evaluate(previous(0), height=30, tag="invalid2")
    count = 0
    visit = _Analyzer.visit

    def counted(self, *args, **kwargs):
        nonlocal count
        count += 1
        return visit(self, *args, **kwargs)

    monkeypatch.setattr(_Analyzer, "visit", counted)
    report = w.check()
    assert {d.tag for d in report.errors} == {"invalid1", "invalid2"}
    assert count < 2000
