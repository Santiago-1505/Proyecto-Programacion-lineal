import math
from core import simplex_utils


def almost_equal(a, b, tol=1e-9):
    return abs(a - b) <= tol


def test_pivot_pure_normaliza_y_elimina():
    # Tableau simple con fila Z + 2 restricciones
    tableau = [
        [0.0, -1.0, -2.0],
        [2.0, 1.0, 0.0],
        [0.0, 1.0, 1.0],
    ]
    terminos = [0.0, 8.0, 4.0]

    # Hacer pivot en (fila 1, col 0) (pivote=2.0)
    tabla_nueva, terminos_nuevos = simplex_utils.pivot_pure(tableau, terminos, 1, 0)

    # Original no debe cambiar
    assert tableau[1][0] == 2.0
    assert terminos[1] == 8.0

    # Nuevo: pivote normalizado a 1 y columna 0 debe ser 0 en otras filas
    assert almost_equal(tabla_nueva[1][0], 1.0)
    assert almost_equal(tabla_nueva[0][0], 0.0)
    assert almost_equal(tabla_nueva[2][0], 0.0)


def test_calcular_razones_alineadas_y_eleccion():
    tableau = [
        [0.0, 0.0],
        [2.0, 1.0],
        [-1.0, 5.0],
    ]
    terminos = [0.0, 10.0, 20.0]

    razones = simplex_utils.calcular_razones_alineadas(tableau, terminos, 0)
    # razones[0] reserved
    assert razones[0] is None
    assert almost_equal(razones[1], 5.0)
    assert razones[2] == float('inf')

    # elegir fila pivote: only row 1 has finite 5.0
    fila = simplex_utils.elegir_fila_pivote_desde_razones(razones)
    assert fila == 1


def test_eliminar_artificiales_de_Z():
    # Z_row tiene coeficiente 10 en columna artificial (col 2)
    Z_row = [1.0, 2.0, 10.0]
    # tabla con una fila de restricción donde la artificial es básica en fila 1
    tabla_full = [Z_row, [0.0, 0.0, 1.0]]
    terminos = [0.0, 7.0]
    indices_art = [2]

    nz, terminoZ = simplex_utils.eliminar_artificiales_de_Z(Z_row, tabla_full, terminos, indices_art)

    # La columna artificial debe quedar 0 y terminoZ ajustado
    assert almost_equal(nz[2], 0.0)
    assert almost_equal(terminoZ, -10.0 * 7.0)
