"""
Análisis de sensibilidad (post-solve) para el solucionador Simplex.

Proporciona una función pura calcular_sensibilidad(solver) que, dado un
SolucionadorSimplex cuya solución final está en solver.iteraciones[-1],
calcula rangos permisibles para los coeficientes de la función objetivo
de las variables de decisión y para los términos independientes (RHS).

La implementación reconstruye la matriz base B a partir de la iteración
inicial y calcula B^{-1} numéricamente. No modifica el estado del solver.
"""
from typing import List, Tuple, Dict, Optional

from core.modelo import Iteracion, Variable, TipoVariable
from core.solucionador_simplex import SolucionadorSimplex


TOL = 1e-12


def _invert_matrix(A: List[List[float]]) -> List[List[float]]:
    """Inversa por Gauss-Jordan con pivoteo parcial. Lanza RuntimeError si
    la matriz es singular dentro de tolerancia.
    """
    n = len(A)
    # Crear copia y matriz identidad
    M = [row[:] for row in A]
    inv = [[float(i == j) for j in range(n)] for i in range(n)]

    for i in range(n):
        # Pivot parcial: buscar fila con mayor valor absoluto en columna i
        piv_row = max(range(i, n), key=lambda r: abs(M[r][i]))
        if abs(M[piv_row][i]) < TOL:
            raise RuntimeError("Matriz singular o casi singular al invertir B")
        # Swap
        if piv_row != i:
            M[i], M[piv_row] = M[piv_row], M[i]
            inv[i], inv[piv_row] = inv[piv_row], inv[i]
        # Normalize pivot row
        piv = M[i][i]
        inv[i] = [v / piv for v in inv[i]]
        M[i] = [v / piv for v in M[i]]
        # Eliminate other rows
        for r in range(n):
            if r == i:
                continue
            factor = M[r][i]
            if factor == 0:
                continue
            M[r] = [mv - factor * iv for mv, iv in zip(M[r], M[i])]
            inv[r] = [rv - factor * iv for rv, iv in zip(inv[r], inv[i])]

    return inv


def _mat_vec_mul(A: List[List[float]], v: List[float]) -> List[float]:
    return [sum(a * x for a, x in zip(row, v)) for row in A]


def _mat_mul(A: List[List[float]], B: List[List[float]]) -> List[List[float]]:
    n = len(A)
    m = len(B[0])
    p = len(B)
    C = [[0.0] * m for _ in range(n)]
    for i in range(n):
        for j in range(m):
            s = 0.0
            for k in range(p):
                s += A[i][k] * B[k][j]
            C[i][j] = s
    return C


def calcular_sensibilidad(solver: SolucionadorSimplex) -> Dict[str, List[Dict]]:
    """
    Calcula análisis de sensibilidad univariado para:
    - coeficientes de la función objetivo de variables de decisión (x1..xn)
    - términos independientes (b1..bm)

    Retorna un diccionario con claves 'coef_objetivo' y 'rhs'. Cada valor es
    una lista de dicts {'parametro': str, 'valor_inicial': float, 'rango': (lo, hi)}
    donde None en los límites representa -inf/+inf.
    """
    if not solver.resuelto:
        raise RuntimeError("El solucionador debe haber alcanzado una solución óptima")
    if solver.es_infactible:
        raise RuntimeError("No aplicable: el problema es infactible")
    if solver.en_fase_1:
        raise RuntimeError("No aplicable: el solucionador aún está en fase 1")

    iter_init: Iteracion = solver.iteraciones[0]
    iter_final: Iteracion = solver.obtener_iteracion_actual()

    # Validaciones básicas
    m = iter_final.obtener_num_restricciones()
    if m <= 0:
        raise RuntimeError("No hay restricciones para analizar")

    nombres = iter_init.nombres_variables_todas
    ncols = len(nombres)

    # Detectar si hay variables artificiales en la base final -> no aplicable
    for vb in iter_final.variables_basicas:
        if vb.tipo == TipoVariable.ARTIFICIAL:
            raise RuntimeError("No aplicable: variables artificiales permanecen en la base")

    # Construir B desde la iteración inicial usando las columnas de las variables básicas finales
    basis_cols: List[int] = [nombres.index(v) for v in iter_final.variables_basicas]

    # Extraer B: columnas correspondientes en iter_init.tableau filas 1..m
    B: List[List[float]] = []
    for row_idx in range(1, m + 1):
        # construir fila de B
        row = [iter_init.tableau[row_idx][col_idx] for col_idx in basis_cols]
        B.append(row)

    # Invertir B
    B_inv = _invert_matrix(B)

    # Número de variables de decisión (primeras columnas con tipo DECISION)
    num_decision = sum(1 for v in nombres if v.tipo == TipoVariable.DECISION)

    # Construir vector c (coeficientes originales de la función objetivo) desde iter_init.fila Z
    fila_z_init = iter_init.tableau[0]
    sign = 1.0 if solver.es_minimizacion else -1.0
    # Según construcción: para max fila_z = -c, para min fila_z = +c
    c = [sign * fila_z_init[j] for j in range(ncols)]

    # c_B: coeficientes objetivo de variables básicas (en el orden de B)
    c_B = [c[col] for col in basis_cols]

    # x_B actual desde iter_final.terminos_independientes filas 1..m
    x_B = [iter_final.terminos_independientes[i] for i in range(1, m + 1)]

    resultado_obj = []

    # Precalcular A_j para todas columnas (desde iter_init filas 1..m)
    A_cols = [[iter_init.tableau[row_idx][j] for row_idx in range(1, m + 1)] for j in range(ncols)]

    # Para cada variable de decisión j, calcular rango
    for j in range(num_decision):
        A_j = A_cols[j]
        # beta_j = B_inv * A_j
        beta_j = _mat_vec_mul(B_inv, A_j)
        # r_j = c_j - c_B^T beta_j
        cBj = sum(cb * bj for cb, bj in zip(c_B, beta_j))
        r_j = c[j] - cBj

        # Si j no es básica -> simple bound Δ ≤ -r_j
        if j not in basis_cols:
            # Δ in (-inf, -r_j]
            lower = None
            upper = -r_j
            rango = (lower, upper)
            resultado_obj.append({
                'parametro': str(nombres[j]),
                'valor_inicial': c[j],
                'rango': rango,
            })
            continue

        # j es básica: encontrar su posición p en B (0..m-1)
        p = basis_cols.index(j)
        # Para cada k no básico (todas las columnas except basis_cols)
        lower_delta = None
        upper_delta = None
        for k in range(ncols):
            if k in basis_cols:
                continue
            A_k = A_cols[k]
            beta_k = _mat_vec_mul(B_inv, A_k)
            # r_k viejo
            cBk = sum(cb * bk for cb, bk in zip(c_B, beta_k))
            r_k = c[k] - cBk
            alpha_k = beta_k[p]
            # Inequality: r_k - Δ * alpha_k ≤ 0  =>  Δ * alpha_k ≥ r_k
            if abs(alpha_k) < TOL:
                # No restricción sobre Δ (a menos que r_k > 0, lo cual indicaría que la base no es óptima)
                continue
            bound = r_k / alpha_k
            if alpha_k > 0:
                # Δ ≥ bound
                if lower_delta is None or bound > lower_delta:
                    lower_delta = bound
            else:
                # alpha_k < 0 -> Δ ≤ bound
                if upper_delta is None or bound < upper_delta:
                    upper_delta = bound

        # Convertir Δ a rango de c_j: [c_j + lower_delta, c_j + upper_delta]
        lo = None if lower_delta is None else c[j] + lower_delta
        hi = None if upper_delta is None else c[j] + upper_delta
        resultado_obj.append({
            'parametro': str(nombres[j]),
            'valor_inicial': c[j],
            'rango': (lo, hi),
        })

    # RHS sensitivity: un cambio en b_t -> x_B_new = x_B + Δ * d where d = B_inv * e_t
    resultado_rhs = []
    for t in range(m):
        # d = t-th column of B_inv
        d = [B_inv[i][t] for i in range(m)]
        lower_delta = None
        upper_delta = None
        for i in range(m):
            di = d[i]
            xi = x_B[i]
            if abs(di) < TOL:
                # No restricción: requerimos xi >= 0
                continue
            bound = -xi / di
            if di > 0:
                # Δ ≥ bound
                if lower_delta is None or bound > lower_delta:
                    lower_delta = bound
            else:
                # di < 0 => Δ ≤ bound
                if upper_delta is None or bound < upper_delta:
                    upper_delta = bound

        lo = None if lower_delta is None else iter_init.terminos_independientes[t + 0 + 1 - 1]  # keep original b_t
        # Above line may look odd but we compute final b-range below
        # Compute actual bounds for b_t
        b0 = iter_init.terminos_independientes[t + 1]
        lo = None if lower_delta is None else b0 + lower_delta
        hi = None if upper_delta is None else b0 + upper_delta
        resultado_rhs.append({
            'parametro': f"b{t+1}",
            'valor_inicial': b0,
            'rango': (lo, hi),
        })

    return {'coef_objetivo': resultado_obj, 'rhs': resultado_rhs, 'meta': {
        'B': B, 'B_inv': B_inv, 'c_B': c_B, 'x_B': x_B,
    }}
