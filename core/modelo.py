from enum import Enum
from dataclasses import dataclass, field


class TipoRestriccion(Enum):
    """Tipos de restricción soportados en el modelo de PL."""
    MENOR_IGUAL = "<="
    MAYOR_IGUAL = ">="
    IGUALDAD = "="

    def __str__(self):
        return self.value

    @classmethod
    def opciones_display(cls) -> list[str]:
        """Retorna las etiquetas legibles para mostrar en el DropBox."""
        return [
            "≤ (Menor o igual)",
            "≥ (Mayor o igual)",
            "= (Igualdad)",
        ]

    @classmethod
    def desde_display(cls, texto: str) -> "TipoRestriccion":
        """Convierte la etiqueta del DropBox al enum correspondiente."""
        mapa = {
            "≤ (Menor o igual)": cls.MENOR_IGUAL,
            "≥ (Mayor o igual)": cls.MAYOR_IGUAL,
            "= (Igualdad)": cls.IGUALDAD,
        }
        return mapa[texto]


@dataclass
class Restriccion:
    """
    Representa una restricción lineal del problema.

    Atributos
    ---------
    lado_izquierdo : str
        Expresión del lado izquierdo de la restricción (p.ej. "2x1 + 3x2").
    tipo           : TipoRestriccion
        Tipo de la restricción (<, >, <=, >=).
    lado_derecho   : str
        Valor numérico del lado derecho como cadena (p.ej. "10").
    """
    lado_izquierdo: str
    tipo: TipoRestriccion
    lado_derecho: str

    def __str__(self) -> str:
        return f"{self.lado_izquierdo}  {self.tipo}  {self.lado_derecho}"

class TipoVariable(Enum):
    DECISION = "x"
    HOLGURA = "S"
    EXCESO = "E"
    ARTIFICIAL = "A"

@dataclass
class Variable:
    tipo: TipoVariable
    indice: int
    es_basica: bool = False

    def __str__(self):
        return f"{self.tipo.value}{self.indice}"

    def __repr__(self):
        return str(self)

@dataclass
class Termino:
    coeficiente: float
    variable: Variable

    def __str__(self):

        coef = (
            ""
            if self.coeficiente == 1
            else "-"
            if self.coeficiente == -1
            else str(self.coeficiente)
        )

        return f"{coef}{self.variable}"

    def __repr__(self):
        return str(self)


@dataclass
class Iteracion:
    """
    Representa una iteración del método simplex.
    
    Atributos:
        numero_iteracion: Número secuencial de la iteración
        tableau: Matriz que incluye restricciones + fila Z
        variables_basicas: Lista de Variable que forman la base actual
        terminos_independientes: Vector b (lado derecho)
        nombres_variables_todas: Lista ordenada de Variable para referencia
        columna_pivote: Índice de columna que entra (para visualización)
        fila_pivote: Índice de fila que sale (para visualización)
        razones_minimo_cociente: Vector de razones para cada fila
        variable_entrante: Variable que entra a la base
        variable_saliente: Variable que sale de la base
    """
    numero_iteracion: int
    tableau: list[list]  # incluyendo fila Z como primera fila
    variables_basicas: list[Variable]
    terminos_independientes: list[float]  # vector b
    nombres_variables_todas: list[Variable] = field(default_factory=list)
    
    # Metadatos de pivotaje para visualización (solo en iteraciones posteriores a la 1ª)
    columna_pivote: int = -1
    fila_pivote: int = -1
    razones_minimo_cociente: list[float] = field(default_factory=list)
    variable_entrante: "Variable | None" = None
    variable_saliente: "Variable | None" = None
    
    def __str__(self):
        return f"Iteración {self.numero_iteracion}"
    
    def obtener_num_restricciones(self) -> int:
        """Retorna cantidad de filas de restricciones (sin contar Z)."""
        return len(self.tableau) - 1
    
    def obtener_num_variables(self) -> int:
        """Retorna cantidad total de columnas."""
        return len(self.tableau[0]) if self.tableau else 0
