from enum import Enum
from dataclasses import dataclass


class TipoRestriccion(Enum):
    """Tipos de restricción soportados en el modelo de PL."""
    MENOR = "<"
    MAYOR = ">"
    MENOR_IGUAL = "<="
    MAYOR_IGUAL = ">="

    def __str__(self):
        return self.value

    @classmethod
    def opciones_display(cls) -> list[str]:
        """Retorna las etiquetas legibles para mostrar en el DropBox."""
        return [
            "< (Menor)",
            "> (Mayor)",
            "≤ (Menor o igual)",
            "≥ (Mayor o igual)",
        ]

    @classmethod
    def desde_display(cls, texto: str) -> "TipoRestriccion":
        """Convierte la etiqueta del DropBox al enum correspondiente."""
        mapa = {
            "< (Menor)":         cls.MENOR,
            "> (Mayor)":         cls.MAYOR,
            "≤ (Menor o igual)": cls.MENOR_IGUAL,
            "≥ (Mayor o igual)": cls.MAYOR_IGUAL,
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