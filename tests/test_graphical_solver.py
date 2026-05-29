from core.graphical_solver import solve_graphical
from core.modelo import Restriccion, TipoRestriccion


def test_simple_max():
    # Maximize Z = 2x1 + 3x2
    # s.t. x1 + x2 <= 5
    #      2x1 + x2 <= 8
    #      x1, x2 >= 0 (implicit)
    objetivo = "2x1 + 3x2"
    tipo = "max"
    restricciones = [
        Restriccion("x1 + x2", TipoRestriccion.MENOR_IGUAL, "5"),
        Restriccion("2x1 + x2", TipoRestriccion.MENOR_IGUAL, "8"),
    ]

    res = solve_graphical(objetivo, tipo, restricciones)
    assert not res.infeasible
    assert res.optimum_point is not None
    # Known solution is x1=0, x2=5 -> Z=15
    ox, oy = res.optimum_point
    assert abs(ox - 0.0) < 1e-6
    assert abs(oy - 5.0) < 1e-6
    assert abs(res.optimum_value - 15.0) < 1e-6
