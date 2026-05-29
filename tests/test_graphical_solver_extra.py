from core.graphical_solver import solve_graphical
from core.modelo import Restriccion, TipoRestriccion


def _close(p, q, eps=1e-6):
    return abs(p[0] - q[0]) <= eps and abs(p[1] - q[1]) <= eps


def test_infeasible_case():
    # x1 + x2 <= 1 and x1 + x2 >= 3 -> infeasible
    objetivo = "x1 + x2"
    tipo = "max"
    restricciones = [
        Restriccion("x1 + x2", TipoRestriccion.MENOR_IGUAL, "1"),
        Restriccion("x1 + x2", TipoRestriccion.MAYOR_IGUAL, "3"),
    ]
    res = solve_graphical(objetivo, tipo, restricciones)
    assert res.infeasible is True


def test_unbounded_case():
    # Single constraint x2 - x1 >= 0 with nonnegativity -> unbounded
    objetivo = "x1 + x2"
    tipo = "max"
    restricciones = [
        Restriccion("x2 - x1", TipoRestriccion.MAYOR_IGUAL, "0"),
    ]
    res = solve_graphical(objetivo, tipo, restricciones)
    assert res.infeasible is False
    # HPI should detect unbounded or at least not bounded
    assert res.is_bounded is False
    # rays should be provided to indicate recession directions
    assert res.rays is not None and len(res.rays) > 0


def test_equality_segment_case():
    # x1 + x2 = 1 intersects nonnegativity axes at (1,0) and (0,1)
    objetivo = "x1 + x2"
    tipo = "max"
    restricciones = [
        Restriccion("x1 + x2", TipoRestriccion.IGUALDAD, "1"),
    ]
    res = solve_graphical(objetivo, tipo, restricciones)
    assert res.infeasible is False
    # Expect points (1,0) and (0,1) as feasible vertices
    found_10 = any(_close(p, (1.0, 0.0)) for p in res.feasible_vertices)
    found_01 = any(_close(p, (0.0, 1.0)) for p in res.feasible_vertices)
    assert found_10 and found_01
