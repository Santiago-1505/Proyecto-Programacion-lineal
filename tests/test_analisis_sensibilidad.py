import unittest

from core.gran_m import ConstructorPrimerIteracion
from core.modelo import Restriccion, TipoRestriccion
from core.solucionador_simplex import SolucionadorSimplex
from core.analisis_sensibilidad import calcular_sensibilidad


class TestAnalisisSensibilidad(unittest.TestCase):

    def test_analisis_basico_devuelve_estructura(self):
        c = ConstructorPrimerIteracion()
        restr = [Restriccion('x1 + x2', TipoRestriccion.MENOR_IGUAL, '5')]
        iter0 = c.construir_tableau_inicial('3x1 + 5x2', 'max', restr)
        solver = SolucionadorSimplex(iter0, es_minimizacion=False)

        # Avanzar hasta resolución
        while solver.puede_avanzar():
            solver.siguiente_iteracion()

        self.assertTrue(solver.resuelto)
        res = calcular_sensibilidad(solver)
        self.assertIn('coef_objetivo', res)
        self.assertIn('rhs', res)
        self.assertIsInstance(res['coef_objetivo'], list)
        self.assertIsInstance(res['rhs'], list)
        # Debe contener filas para x1 y x2
        nombres = [r['parametro'] for r in res['coef_objetivo']]
        self.assertIn('x1', nombres)
        self.assertIn('x2', nombres)


if __name__ == '__main__':
    unittest.main()
