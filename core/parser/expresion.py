from core.modelo import Termino, Variable, TipoVariable
import re

def parsear_terminos(texto: str) -> list[Termino]:

    texto = texto.replace(" ", "")

    patron = r'([+-]?\d*\.?\d*)x(\d+)'

    terminos = []

    for coef, indice in re.findall(patron, texto):

        # x1
        if coef in ("", "+"):
            coeficiente = 1

        # -x1
        elif coef == "-":
            coeficiente = -1

        else:
            coeficiente = float(coef)

        variable = Variable(
            tipo=TipoVariable.DECISION,
            indice=int(indice)
        )

        terminos.append(
            Termino(
                coeficiente,
                variable
            )
        )

    return terminos
