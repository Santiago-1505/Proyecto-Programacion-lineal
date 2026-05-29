import unittest

from core.gran_m import ConstructorPrimerIteracion
from core.modelo import Restriccion, TipoRestriccion
from core.solucionador_simplex import SolucionadorSimplex


class TestExtraSolverCases(unittest.TestCase):

    def test_minimization_basic(self):
        # min x1 + x2 subject to x1 + x2 >= 5  (min = 5)
        c = ConstructorPrimerIteracion()
        restr = [Restriccion('x1 + x2', TipoRestriccion.MAYOR_IGUAL, '5')]
        iter0 = c.construir_tableau_inicial('x1 + x2', 'min', restr)
        solver = SolucionadorSimplex(iter0, es_minimizacion=True)

        # Avanzar hasta resolución o excepción
        # Para este problema la solución debe existir y ser 5
        while solver.puede_avanzar():
            solver.siguiente_iteracion()

        # Verificar que la iteración final tenga el valor objetivo esperado
        ultima = solver.obtener_iteracion_actual()
        # El término independiente de Z para este problema debe ser 5
        self.assertAlmostEqual(ultima.terminos_independientes[0], 5.0, places=6)

    def test_detecta_ilimitado_simple(self):
        # maximize x1 with constraint x1 >= 1 -> ilimitado
        c = ConstructorPrimerIteracion()
        restr = [Restriccion('x1', TipoRestriccion.MAYOR_IGUAL, '1')]
        iter0 = c.construir_tableau_inicial('x1', 'max', restr)
        solver = SolucionadorSimplex(iter0, es_minimizacion=False)

        # Al intentar avanzar, debe detectarse ilimitado y lanzar RuntimeError
        with self.assertRaises(RuntimeError):
            while solver.puede_avanzar():
                solver.siguiente_iteracion()

        self.assertTrue(solver.es_ilimitado)

    def test_artificial_equality_and_solution(self):
        # maximize x1 subject to x1 + x2 = 5 -> optimal x1=5
        c = ConstructorPrimerIteracion()
        restr = [Restriccion('x1 + x2', TipoRestriccion.IGUALDAD, '5')]
        iter0 = c.construir_tableau_inicial('x1', 'max', restr)
        solver = SolucionadorSimplex(iter0, es_minimizacion=False)

        # Debe entrar en fase 1 inicialmente (artificial en la base)
        self.assertTrue(solver.en_fase_1)

        # Ejecutar iteraciones hasta resolver o error
        try:
            while solver.puede_avanzar():
                solver.siguiente_iteracion()
        except RuntimeError as e:
            # Si hay error, dejar que el test lo reporte apropiadamente
            self.fail(f"Solver lanzó excepción inesperada: {e}")

        ultima = solver.obtener_iteracion_actual()
        # Verificar que la solución óptima del objetivo sea 5
        self.assertAlmostEqual(ultima.terminos_independientes[0], 5.0, places=6)


if __name__ == '__main__':
    unittest.main()
