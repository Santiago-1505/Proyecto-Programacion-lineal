from core.modelo import Termino, Variable, TipoVariable
import re


def parsear_terminos(texto: str) -> list[Termino]:
    """
    Parsea una expresión y retorna lista de objetos Termino.
    
    Ejemplo: "2x1 + 3x2 - x3" → [Termino(2, x1), Termino(3, x2), Termino(-1, x3)]
    
    Args:
        texto: Expresión con formato "coefx_indice ± coefx_indice ..."
    
    Returns:
        Lista de objetos Termino parseados
    """
    texto = texto.replace(" ", "")
    patron = r'([+-]?\d*\.?\d*)x(\d+)'
    terminos = []

    for coef, indice in re.findall(patron, texto):
        # x1 o +x1
        if coef in ("", "+"):
            coeficiente = 1.0
        # -x1
        elif coef == "-":
            coeficiente = -1.0
        else:
            coeficiente = float(coef)

        variable = Variable(
            tipo=TipoVariable.DECISION,
            indice=int(indice)
        )

        terminos.append(Termino(coeficiente, variable))

    return terminos


def obtener_max_indice_variable(expresion: str) -> int:
    """
    Determina el máximo índice de variable en una expresión.
    
    Ejemplo: "2x1 + 3x5" → 5
    
    Args:
        expresion: Expresión con variables xN
    
    Returns:
        Máximo índice encontrado, 0 si no hay variables
    """
    expresion = expresion.replace(" ", "")
    indices = re.findall(r'x(\d+)', expresion)
    
    if not indices:
        return 0
    
    return max(int(i) for i in indices)


def vectorizar_expresion(expresion: str, num_variables: int, tipo_variable: TipoVariable = TipoVariable.DECISION) -> list[float]:
    """
    Convierte una expresión en un vector numérico de coeficientes.
    
    Ejemplo: "2x1 + 5x3" con num_variables=3 → [2.0, 0.0, 5.0]
    
    Args:
        expresion: Expresión con variables
        num_variables: Número total de variables esperadas
        tipo_variable: Tipo de variable a extraer (DECISION por defecto)
    
    Returns:
        Vector de coeficientes con tamaño num_variables
    """
    vector = [0.0] * num_variables
    terminos = parsear_terminos(expresion)
    
    for termino in terminos:
        # El índice de la variable comienza desde 1, pero el vector desde 0
        indice = termino.variable.indice - 1
        
        # Validar que el índice esté dentro del rango
        if 0 <= indice < num_variables:
            vector[indice] = termino.coeficiente
    
    return vector
