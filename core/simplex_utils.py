"""
Utilidades puras para operaciones del método simplex.

Contiene funciones que realizan pivotajes y cálculos sin mutar las
estructuras de entrada. Estas funciones devuelven nuevas estructuras
para garantizar que las iteraciones previas permanezcan inmutables.
"""
from copy import deepcopy
from typing import Tuple, List


def copiar_tableau(tableau: list[list[float]]) -> list[list[float]]:
    """Devuelve una copia profunda del tableau (listas de filas)."""
    return [fila[:] for fila in tableau]


def pivot_pure(
    tableau: list[list[float]],
    terminos: list[float],
    fila_pivote: int,
    columna_pivote: int,
) -> Tuple[list[list[float]], list[float]]:
    """
    Realiza un pivote sobre copias del tableau y términos independientes.

    Args:
        tableau: matriz con fila Z en la posición 0 y restricciones en 1..m
        terminos: vector b con longitud igual a len(tableau)
        fila_pivote: índice de fila del pivote (0..m)
        columna_pivote: índice de columna del pivote (0..n-1)

    Returns:
        (nuevo_tableau, nuevos_terminos)

    Lanza RuntimeError si el pivote es cero dentro de tolerancia.
    """
    # Copias defensivas
    ntableau = copiar_tableau(tableau)
    nterminos = terminos[:]  # copia superficial suficiente (floats)

    # Validar dimensiones
    if not ntableau:
        raise RuntimeError("Tableau vacío en pivot_pure")

    if len(nterminos) != len(ntableau):
        raise RuntimeError("Vector de términos con longitud inconsistente")

    piv = ntableau[fila_pivote][columna_pivote]
    if abs(piv) < 1e-12:
        raise RuntimeError(f"Pivote demasiado pequeño: {piv}")

    # Normalizar fila pivote
    ncols = len(ntableau[0])
    for j in range(ncols):
        ntableau[fila_pivote][j] /= piv
    nterminos[fila_pivote] /= piv

    # Eliminar en otras filas
    for i in range(len(ntableau)):
        if i == fila_pivote:
            continue
        factor = -ntableau[i][columna_pivote]
        if factor == 0:
            continue
        # Operar sobre cada columna
        for j in range(ncols):
            ntableau[i][j] += factor * ntableau[fila_pivote][j]
        nterminos[i] += factor * nterminos[fila_pivote]

    return ntableau, nterminos


def calcular_razones_alineadas(tableau: list[list[float]], terminos: list[float], columna_entrante: int) -> list[float]:
    """
    Calcula el vector de razones (mínimo cociente) y lo devuelve alineado con
    las filas del tableau: razones[0] es None (fila Z), razones[1..m] corresponden
    a las filas de restricciones.

    Regla: si a_ij > 0 -> razón = b_i / a_ij, si a_ij <= 0 -> inf
    """
    m = len(tableau) - 1
    razones: list[float] = [None] * (m + 1)

    tol = 1e-12
    for i in range(1, m + 1):
        a_ij = tableau[i][columna_entrante]
        b_i = terminos[i]
        # Distinción: positive divisor => numeric ratio
        # zero divisor => None (display as "—")
        # negative divisor => +inf (display as "∞")
        if a_ij > tol:
            razones[i] = b_i / a_ij
        elif abs(a_ij) <= tol:
            razones[i] = None
        else:
            razones[i] = float('inf')

    return razones


def elegir_fila_pivote_desde_razones(razones: list[float]) -> int | None:
    """
    Dado el vector de razones alineadas (razones[0]=None), retorna el índice de
    la fila pivote que minimiza la razón. Retorna None si no hay divisor positivo
    (todas inf).
    """
    fila = None
    valor_min = float('inf')
    for i in range(1, len(razones)):
        r = razones[i]
        if r is None:
            continue
        if r < valor_min:
            valor_min = r
            fila = i
    return fila


def eliminar_artificiales_de_Z(
    Z_row: list[float],
    tableau: list[list[float]],
    terminos: list[float],
    indices_artificiales: list[int]
) -> tuple[list[float], float]:
    """
    Ajusta la fila Z para eliminar el efecto de las variables artificiales que
    están en la base mediante la operación Z <- Z - coef_Z_ai * fila_i.

    indices_artificiales: lista de índices de columna que son artificiales.

    Retorna (Z_row_ajustada, terminoZ) donde terminoZ es el término independiente
    de Z (escalar). Nota: asumimos que Z_row no incluye el término independiente
    y que tableau contiene las filas de restricciones con su b en 'terminos'.
    """
    nz = Z_row[:]
    terminoZ = 0.0

    # Por cada fila de restricción, si su variable básica es artificial (col en indices),
    # eliminar su contribución en Z
    # Buscamos en cada columna artificial el coef en Z y, si no es cero, restamos coef * fila
    for col in indices_artificiales:
        coefZ = nz[col]
        if coefZ == 0:
            continue
        # Buscar fila donde esa artificial es básica (columna con 1 en esa fila y 0 en otras)
        fila_en_base = None
        for i in range(1, len(tableau)):
            if abs(tableau[i][col] - 1.0) < 1e-12:
                fila_en_base = i
                break
        if fila_en_base is None:
            # No está en la base de forma canónica; no podemos eliminar usando esa fila
            continue
        # Z <- Z - coefZ * row_fila_en_base
        for j in range(len(nz)):
            nz[j] -= coefZ * tableau[fila_en_base][j]
        terminoZ -= coefZ * terminos[fila_en_base]

    return nz, terminoZ


def validar_consistencia_iteracion(tableau: list[list[float]], terminos: list[float], variables_basicas: list, nombres_variables: list, razones: list | None = None) -> None:
    """
    Verifica invariantes básicas del tableau/iteración y lanza RuntimeError con
    mensaje explicativo si algo no cuadra.
    """
    if not tableau:
        raise RuntimeError("Tableau vacío")
    if len(terminos) != len(tableau):
        raise RuntimeError("Vector de términos independiente desalineado con tableau")
    if len(tableau[0]) != len(nombres_variables):
        raise RuntimeError("Número de columnas no coincide con nombres de variables")
    if len(variables_basicas) != len(tableau) - 1:
        raise RuntimeError("Lista de variables básicas no coincide con número de restricciones")
    if razones is not None and len(razones) != len(tableau):
        raise RuntimeError("Vector de razones no está alineado con filas del tableau")
