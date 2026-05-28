"""
Ejemplos de uso de la API del solver de programación lineal.

Este archivo muestra cómo usar el solver sin GUI.
"""

from core.gran_m import ConstructorPrimerIteracion
from core.modelo import Restriccion, TipoRestriccion
from core.solucionador_simplex import SolucionadorSimplex
from ui.formateador_tableau import FormateadorTableau


def ejemplo_1_simple():
    """
    Ejemplo 1: Problema simple con solo restricciones <=
    
    Maximizar: Z = 2x1 + 3x2
    Sujeto a:
        x1 + x2 <= 5
        2x1 + x2 <= 8
        x1, x2 >= 0
    """
    print("\n" + "="*60)
    print("EJEMPLO 1: Problema Simple (Solo restricciones <=)")
    print("="*60)
    
    objetivo = "2x1 + 3x2"
    tipo_opt = "max"
    restricciones = [
        Restriccion("x1 + x2", TipoRestriccion.MENOR_IGUAL, "5"),
        Restriccion("2x1 + x2", TipoRestriccion.MENOR_IGUAL, "8"),
    ]
    
    # Construir tableau
    constructor = ConstructorPrimerIteracion()
    iteracion = constructor.construir_tableau_inicial(objetivo, tipo_opt, restricciones)
    
    # Mostrar información
    print(f"\nProblema:")
    print(f"  Objetivo: {objetivo} ({tipo_opt.upper()})")
    print(f"  Restricciones: {len(restricciones)}")
    
    # Obtener datos formateados
    datos = FormateadorTableau.obtener_datos_tabla(iteracion)
    
    print(f"\nTableau Inicial:")
    print(f"  Variables: {', '.join(datos['encabezados'])}")
    print(f"  Variables básicas: {', '.join(datos['variables_basicas'])}")
    
    print(f"\n  Matriz:")
    for i, fila in enumerate(datos['datos']):
        print(f"    {datos['filas'][i]:3} {' '.join(f'{v:>8}' for v in fila)} | {datos['terminos_independientes'][i]:>8}")
    
    print(f"\nCaracterísticas:")
    print(f"  - Total de variables: {iteracion.obtener_num_variables()}")
    print(f"  - Total de restricciones: {iteracion.obtener_num_restricciones()}")
    print(f"  - Variables de holgura: {len([v for v in datos['encabezados'] if v.startswith('S')])}")


def ejemplo_2_con_artificiales():
    """
    Ejemplo 2: Problema con restricciones >= e =
    
    Minimizar: Z = 3x1 + 2x2
    Sujeto a:
        x1 + x2 >= 4
        2x1 + x2 = 6
        x1, x2 >= 0
    """
    print("\n" + "="*60)
    print("EJEMPLO 2: Problema con Artificiales (>= e =)")
    print("="*60)
    
    objetivo = "3x1 + 2x2"
    tipo_opt = "min"
    restricciones = [
        Restriccion("x1 + x2", TipoRestriccion.MAYOR_IGUAL, "4"),
        Restriccion("2x1 + x2", TipoRestriccion.IGUALDAD, "6"),
    ]
    
    # Construir tableau
    constructor = ConstructorPrimerIteracion()
    iteracion = constructor.construir_tableau_inicial(objetivo, tipo_opt, restricciones)
    
    print(f"\nProblema:")
    print(f"  Objetivo: {objetivo} ({tipo_opt.upper()})")
    print(f"  Restricciones: {len(restricciones)}")
    
    datos = FormateadorTableau.obtener_datos_tabla(iteracion)
    
    print(f"\nTableau Inicial (con variables artificiales):")
    print(f"  Variables: {', '.join(datos['encabezados'])}")
    print(f"  Variables básicas: {', '.join(datos['variables_basicas'])}")
    
    print(f"\n  Matriz:")
    for i, fila in enumerate(datos['datos']):
        print(f"    {datos['filas'][i]:3} {' '.join(f'{v:>8}' for v in fila)} | {datos['terminos_independientes'][i]:>8}")
    
    print(f"\nCaracterísticas:")
    print(f"  - Total de variables: {iteracion.obtener_num_variables()}")
    print(f"  - Variables de exceso: {len([v for v in datos['encabezados'] if v.startswith('E')])}")
    print(f"  - Variables artificiales: {len([v for v in datos['encabezados'] if v.startswith('A')])}")
    print(f"  - Penalización M en fila Z: Sí")


def ejemplo_3_mixto():
    """
    Ejemplo 3: Problema con todos los tipos de restricciones
    
    Maximizar: Z = x1 + x2 + x3
    Sujeto a:
        x1 + x2 + x3 <= 10
        2x1 + x2 >= 5
        x1 + 2x3 = 8
        x1, x2, x3 >= 0
    """
    print("\n" + "="*60)
    print("EJEMPLO 3: Problema Mixto (Todos los tipos de restricción)")
    print("="*60)
    
    objetivo = "x1 + x2 + x3"
    tipo_opt = "max"
    restricciones = [
        Restriccion("x1 + x2 + x3", TipoRestriccion.MENOR_IGUAL, "10"),
        Restriccion("2x1 + x2", TipoRestriccion.MAYOR_IGUAL, "5"),
        Restriccion("x1 + 2x3", TipoRestriccion.IGUALDAD, "8"),
    ]
    
    constructor = ConstructorPrimerIteracion()
    iteracion = constructor.construir_tableau_inicial(objetivo, tipo_opt, restricciones)
    
    print(f"\nProblema:")
    print(f"  Objetivo: {objetivo} ({tipo_opt.upper()})")
    print(f"  Restricciones:")
    for i, r in enumerate(restricciones, 1):
        print(f"    R{i}: {r}")
    
    datos = FormateadorTableau.obtener_datos_tabla(iteracion)
    
    print(f"\nTableau Inicial:")
    print(f"  Variables: {', '.join(datos['encabezados'])}")
    print(f"  Variables básicas: {', '.join(datos['variables_basicas'])}")
    
    print(f"\n  Matriz:")
    for i, fila in enumerate(datos['datos']):
        print(f"    {datos['filas'][i]:3} {' '.join(f'{v:>8}' for v in fila)} | {datos['terminos_independientes'][i]:>8}")
    
    print(f"\nAnalisis de Variables:")
    var_s = [v for v in datos['encabezados'] if v.startswith('S')]
    var_e = [v for v in datos['encabezados'] if v.startswith('E')]
    var_a = [v for v in datos['encabezados'] if v.startswith('A')]
    print(f"  - Holgura: {', '.join(var_s) if var_s else 'Ninguna'}")
    print(f"  - Exceso: {', '.join(var_e) if var_e else 'Ninguna'}")
    print(f"  - Artificiales: {', '.join(var_a) if var_a else 'Ninguna'}")


def ejemplo_4_uso_solucionador():
    """
    Ejemplo 4: Uso del solucionador para gestionar iteraciones
    """
    print("\n" + "="*60)
    print("EJEMPLO 4: Uso del Solucionador")
    print("="*60)
    
    objetivo = "5x1 + 4x2"
    tipo_opt = "max"
    restricciones = [
        Restriccion("x1 + 2x2", TipoRestriccion.MENOR_IGUAL, "12"),
        Restriccion("2x1 + x2", TipoRestriccion.MENOR_IGUAL, "12"),
    ]
    
    # Construir tableau inicial
    constructor = ConstructorPrimerIteracion()
    iteracion = constructor.construir_tableau_inicial(objetivo, tipo_opt, restricciones)
    
    # Crear solucionador
    es_minimizacion = (tipo_opt.lower() == "min")
    solucionador = SolucionadorSimplex(iteracion, es_minimizacion)
    
    print(f"\nSolucionador inicializado:")
    print(f"  - Iteración actual: {solucionador.iteracion_actual}")
    print(f"  - Total de iteraciones: {len(solucionador.iteraciones)}")
    print(f"  - Puede avanzar: {solucionador.puede_avanzar()}")
    print(f"  - Resuelto: {solucionador.resuelto}")
    
    iter_act = solucionador.obtener_iteracion_actual()
    datos = FormateadorTableau.obtener_datos_tabla(iter_act)
    
    print(f"\nIteración actual #{solucionador.iteracion_actual + 1}:")
    print(f"  Variables básicas: {', '.join(datos['variables_basicas'])}")
    print(f"  Valor actual de Z: {datos['terminos_independientes'][0]}")


def main():
    """Ejecuta todos los ejemplos."""
    print("\n" + "█"*60)
    print("█ EJEMPLOS DE USO DEL SOLVER DE PROGRAMACIÓN LINEAL")
    print("█"*60)
    
    try:
        ejemplo_1_simple()
        ejemplo_2_con_artificiales()
        ejemplo_3_mixto()
        ejemplo_4_uso_solucionador()
        
        print("\n" + "█"*60)
        print("█ TODOS LOS EJEMPLOS SE EJECUTARON CORRECTAMENTE ✓")
        print("█"*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
