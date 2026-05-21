"""
GUÍA RÁPIDA - Solver de Programación Lineal

Acceso rápido a funciones principales y ejemplos de uso.
"""

# ═══════════════════════════════════════════════════════════════════════════════
# EJECUTAR LA APLICACIÓN
# ═══════════════════════════════════════════════════════════════════════════════

# Opción 1: Interfaz Gráfica (GUI)
# $ python main.py

# Opción 2: Ver ejemplos en consola
# $ python ejemplos.py

# Opción 3: Usar como librería Python


# ═══════════════════════════════════════════════════════════════════════════════
# USO COMO LIBRERÍA
# ═══════════════════════════════════════════════════════════════════════════════

from core.gran_m import ConstructorPrimerIteracion
from core.modelo import Restriccion, TipoRestriccion
from ui.formateador_tableau import FormateadorTableau

# Paso 1: Definir el problema
objetivo = "2x1 + 3x2"           # Función objetivo
tipo_opt = "max"                  # Tipo: "max" o "min"
restricciones = [
    Restriccion("x1 + x2", TipoRestriccion.MENOR_IGUAL, "5"),
    Restriccion("2x1 + x2", TipoRestriccion.MENOR_IGUAL, "8"),
]

# Paso 2: Construir tableau inicial
constructor = ConstructorPrimerIteracion()
iteracion = constructor.construir_tableau_inicial(objetivo, tipo_opt, restricciones)

# Paso 3: Obtener datos formateados
datos = FormateadorTableau.obtener_datos_tabla(iteracion)

# Paso 4: Acceder a la información
print("Variables:", datos['encabezados'])
print("Variables básicas:", datos['variables_basicas'])
print("Matriz:")
for i, fila in enumerate(datos['datos']):
    print(f"  {datos['filas'][i]}: {fila}")


# ═══════════════════════════════════════════════════════════════════════════════
# FORMATO DE ENTRADA - EJEMPLOS VÁLIDOS
# ═══════════════════════════════════════════════════════════════════════════════

# EXPRESIONES (Función Objetivo o Lado Izquierdo de Restricción):
#   "2x1 + 3x2"         → válido
#   "-x1 + 5x2"         → válido (coef = -1)
#   "x1 - 2x3"          → válido (resta)
#   "4x2"               → válido (una variable)
#   "2x1 - x2 + 3x5"    → válido (índices no consecutivos)

# TIPOS DE RESTRICCIÓN:
#   "<=" → Menor o igual (agrega variable de holgura)
#   ">=" → Mayor o igual (agrega variable de exceso + artificial)
#   "=" → Igualdad (agrega variable artificial)

# LADO DERECHO:
#   "5", "10.5", "0"    → Solo números positivos o cero


# ═══════════════════════════════════════════════════════════════════════════════
# TIPOS DE RESTRICCIÓN - TRANSFORMACIONES AUTOMÁTICAS
# ═══════════════════════════════════════════════════════════════════════════════

# Restricción <=:
#   Entrada:   x1 + x2 <= 5
#   Tableau:   x1 + x2 + S1 = 5
#   Variable básica: S1 (holgura)

# Restricción >=:
#   Entrada:   x1 + x2 >= 5
#   Tableau:   x1 + x2 - E1 + A1 = 5
#   Variable básica: A1 (artificial, con penalización M)

# Restricción =:
#   Entrada:   x1 + x2 = 5
#   Tableau:   x1 + x2 + A1 = 5
#   Variable básica: A1 (artificial, con penalización M)


# ═══════════════════════════════════════════════════════════════════════════════
# ESTRUCTURA DE DATOS CLAVE
# ═══════════════════════════════════════════════════════════════════════════════

# Clase: Variable
#   Propiedades:
#   - tipo: TipoVariable (DECISION, HOLGURA, EXCESO, ARTIFICIAL)
#   - indice: int (1, 2, 3, ...)
#   Ejemplo: Variable(TipoVariable.DECISION, 1) → "x1"

# Clase: Restriccion
#   Propiedades:
#   - lado_izquierdo: str (expresión)
#   - tipo: TipoRestriccion (MENOR_IGUAL, MAYOR_IGUAL, IGUALDAD)
#   - lado_derecho: str (número)

# Clase: Iteracion
#   Propiedades:
#   - numero_iteracion: int
#   - tableau: list[list] (matriz del tableau)
#   - variables_basicas: list[Variable] (base actual)
#   - terminos_independientes: list[float] (vector b)
#   - nombres_variables_todas: list[Variable]
#   Métodos:
#   - obtener_num_variables(): int
#   - obtener_num_restricciones(): int


# ═══════════════════════════════════════════════════════════════════════════════
# SIGNIFICADO DE LAS VARIABLES EN EL TABLEAU
# ═══════════════════════════════════════════════════════════════════════════════

# x1, x2, x3, ... 
#   - Variables de decisión (ingresadas por el usuario)
#   - Representadas como "x<número>"

# S1, S2, S3, ...
#   - Variables de holgura
#   - Agregadas para restricciones <= 
#   - Coeficiente: +1

# E1, E2, E3, ...
#   - Variables de exceso
#   - Agregadas para restricciones >=
#   - Coeficiente: -1

# A1, A2, A3, ...
#   - Variables artificiales
#   - Agregadas para restricciones >= y =
#   - Coeficiente: +1
#   - Penalizadas con M en la función objetivo

# M
#   - Constante grande de penalización
#   - Representada como símbolo literal (no numérico)
#   - Permite forzar variables artificiales a 0 en la solución


# ═══════════════════════════════════════════════════════════════════════════════
# EJEMPLO COMPLETO PASO A PASO
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 70)
    print("EJEMPLO: Resolver Problema de Programación Lineal")
    print("=" * 70)
    
    # Definir problema: Maximizar 2x1 + 3x2 sujeto a restricciones
    print("\nProblema:")
    print("  Maximizar: Z = 2x1 + 3x2")
    print("  Sujeto a:")
    print("    x1 + x2 <= 5")
    print("    2x1 + x2 <= 8")
    print("    x1, x2 >= 0")
    
    # Crear restricciones
    r1 = Restriccion("x1 + x2", TipoRestriccion.MENOR_IGUAL, "5")
    r2 = Restriccion("2x1 + x2", TipoRestriccion.MENOR_IGUAL, "8")
    
    # Construir tableau
    constructor = ConstructorPrimerIteracion()
    iteracion = constructor.construir_tableau_inicial(
        objetivo="2x1 + 3x2",
        tipo_optimizacion="max",
        restricciones=[r1, r2]
    )
    
    # Obtener datos
    datos = FormateadorTableau.obtener_datos_tabla(iteracion)
    
    # Mostrar resultado
    print("\nTableau Simplex Inicial:")
    print("Variables:", " ".join(f"{v:>6}" for v in datos['encabezados']))
    print("-" * 50)
    
    for i, fila in enumerate(datos['datos']):
        etiqueta = datos['filas'][i]
        valores = " ".join(f"{v:>6}" for v in fila)
        termino = datos['terminos_independientes'][i]
        print(f"{etiqueta:2} | {valores} | {termino:>6}")
    
    print("\nVariables Básicas:")
    for restriccion, var_basica in zip(datos['filas'][1:], datos['variables_basicas']):
        print(f"  {restriccion}: {var_basica}")
    
    print("\n✓ Tableau construido exitosamente")
    print("✓ Listo para aplicar algoritmo de pivoteo (en desarrollo)")


# ═══════════════════════════════════════════════════════════════════════════════
# TROUBLESHOOTING - ERRORES COMUNES
# ═══════════════════════════════════════════════════════════════════════════════

# Error: "ValueError: No se encontraron variables de decisión"
# Solución: Revisar que la expresión contenga al menos una variable (ej: x1)

# Error: "ValueError: Debe haber al menos una restricción"
# Solución: Agregar al menos una restricción

# Error: "ValueError: Lado derecho debe ser numérico"
# Solución: El lado derecho debe ser un número (ej: "5" no "cinco")

# Error: "IndexError" en visualización
# Solución: Verificar que todos los inputs sean válidos


# ═══════════════════════════════════════════════════════════════════════════════
# REFERENCIAS Y DOCUMENTACIÓN
# ═══════════════════════════════════════════════════════════════════════════════

# Ver más ejemplos: python ejemplos.py
# Ver README completo: cat README.md
# Ver estructura: ls -la core/ ui/
