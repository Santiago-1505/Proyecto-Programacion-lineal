# Proyecto Programacion Lineal - Metodo Simplex

**Integrantes:** Ricardo Medina y Santiago Villegas

**Materia:** Optimizacion

---

## Descripcion

Aplicacion de escritorio para resolver problemas de programacion lineal utilizando el metodo Simplex (Gran M) y metodo grafico para dos variables. Incluye visualizacion iterativa del tableau, analisis de sensibilidad y representacion grafica de la region factible.

---

## Requisitos

- Python 3.13 o superior
- Matplotlib (para el metodo grafico)

## Instalacion y ejecucion

Instalar dependencia de Matplotlib:

```bash
pip install matplotlib
```

Ejecutar la aplicacion:

```bash
python main.py
```

---

## Arquitectura del proyecto

```
Proyecto-Programacion-lineal/
|-- core/                     # Logica central del metodo simplex
|   |-- modelo.py             # Dataclasses y enumeradores (Restriccion, Variable, etc.)
|   |-- parser/expresion.py   # Parser de expresiones matematicas
|   |-- gran_m.py             # Construccion del tableau inicial (Metodo Gran M)
|   |-- simplex_utils.py      # Operaciones del simplex (pivote, razones)
|   |-- solucionador_simplex.py  # Orquestador del algoritmo simplex iterativo
|   |-- analisis_sensibilidad.py # Analisis de sensibilidad post-solucion
|   |-- graphical_solver.py   # Solver grafico para problemas de 2 variables
|-- ui/                       # Interfaz de usuario (tkinter)
|   |-- ventana_principal.py  # Ventana principal con layout y controladores
|   |-- panel_entrada.py      # Panel izquierdo: formulario de entrada
|   |-- panel_resultado.py    # Panel derecho: muestra tableau y sensibilidad
|   |-- panel_grafico.py      # Panel grafico con matplotlib incrustado
|   |-- tabla_simplex.py      # Componente Treeview para el tableau
|   |-- formateador_tableau.py  # Formato para visualizacion del tableau
|   |-- widgets/
|       |-- fila_restriccion.py  # Widget de fila de restriccion
|-- tests/                    # Pruebas unitarias
|-- main.py                   # Punto de entrada de la aplicacion
```

**Flujo de ejecucion:**

1. `main.py` inicia la ventana principal (`VentanaPrincipal` en tkinter).
2. El usuario ingresa la funcion objetivo, restricciones y selecciona el metodo en el `PanelEntrada`.
3. Al presionar "Resolver", se construye el tableau inicial (`ConstructorPrimerIteracion`) y se crea el `SolucionadorSimplex`.
4. El usuario avanza iteracion por iteracion con el boton "Siguiente Iteracion", viendo el tableau actualizado en `TablaSimplex`.
5. Al alcanzar el optimo, se puede ejecutar el analisis de sensibilidad.
6. Para problemas de 2 variables, el metodo grafico utiliza `solve_graphical()` y renderiza la region factible con matplotlib.
