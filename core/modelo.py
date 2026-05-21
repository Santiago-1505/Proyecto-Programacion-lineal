from enum import Enum
from dataclasses import dataclass


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
    HOLGURA = "h"
    EXCESO = "e"
    ARTIFICIAL = "a"

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