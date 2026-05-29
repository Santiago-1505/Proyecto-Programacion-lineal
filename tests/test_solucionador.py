import unittest

from core.gran_m import ConstructorPrimerIteracion
from core.modelo import Restriccion, TipoRestriccion
from core.solucionador_simplex import SolucionadorSimplex


class TestSolucionadorSimplex(unittest.TestCase):

    def test_max_simple_lp(self):
        # max 3x1 + 5x2 s.t. x1 + x2 <= 5  -> optimal 25 at x2=5
        c = ConstructorPrimerIteracion()
        restr = [Restriccion('x1 + x2', TipoRestriccion.MENOR_IGUAL, '5')]
        iter0 = c.construir_tableau_inicial('3x1 + 5x2', 'max', restr)
        solver = SolucionadorSimplex(iter0, es_minimizacion=False)

        # Avanzar hasta resolución o error
        while solver.puede_avanzar():
            solver.siguiente_iteracion()

        self.assertTrue(solver.resuelto)
        ultima = solver.obtener_iteracion_actual()
        # El término independiente de Z debe coincidir con la óptima (25)
        self.assertAlmostEqual(ultima.terminos_independientes[0], 25.0, places=7)

    def test_inmutabilidad_iteraciones(self):
        # Verifica que iteraciones previas no se mutan al avanzar
        c = ConstructorPrimerIteracion()
        restr = [Restriccion('x1 + x2', TipoRestriccion.MENOR_IGUAL, '5')]
        iter0 = c.construir_tableau_inicial('3x1 + 5x2', 'max', restr)
        copy_tableau = [row[:] for row in iter0.tableau]

        solver = SolucionadorSimplex(iter0, es_minimizacion=False)
        # Avanzar una iteración
        if solver.puede_avanzar():
            solver.siguiente_iteracion()

        # La tabla original debe permanecer igual
        self.assertEqual(copy_tableau, iter0.tableau)

    def test_detecta_infactibilidad(self):
        # Sistema contradictorio: x1 <= 0 y x1 >= 1 -> infactible
        c = ConstructorPrimerIteracion()
        restr = [
            Restriccion('x1', TipoRestriccion.MENOR_IGUAL, '0'),
            Restriccion('x1', TipoRestriccion.MAYOR_IGUAL, '1')
        ]
        iter0 = c.construir_tableau_inicial('x1', 'max', restr)
        solver = SolucionadorSimplex(iter0, es_minimizacion=False)

        # Intentar avanzar debe terminar marcando infactible (posible excepción)
        with self.assertRaises(RuntimeError) as cm:
            # llamar siguiente_iteracion hasta que detecte infactible
            while solver.puede_avanzar():
                solver.siguiente_iteracion()

        self.assertTrue('infactible' in str(cm.exception).lower())


if __name__ == '__main__':
    unittest.main()
