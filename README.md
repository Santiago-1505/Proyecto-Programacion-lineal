# Proyecto: Solver de Programación Lineal - Método Gran M

Una aplicación interactiva para resolver problemas de programación lineal mediante el método simplex con la técnica de la Gran M (artificial variables).

## Características

### Fase 1 - ✅ Completa: Construcción del Tableau Inicial

- **Parser flexible**: Ingresa expresiones como `2x1 + 3x2 - x3`
- **Tres tipos de restricción**:
  - `<=` (Menor o igual) - Agrega variable de holgura
  - `>=` (Mayor o igual) - Agrega variable de exceso + artificial
  - `=` (Igualdad) - Agrega variable artificial
- **Optimización**: Soporte para maximización y minimización
- **Tableau visual**: 
  - Tabla formateada con precisión de 2 decimales
  - Representación simbólica de la constante M
  - Variables básicas destacadas
  - Scroll automático para problemas grandes

### Fase 2 - ⏳ Próxima: Algoritmo de Pivoteo

- Selección de columna pivote
- Selección de fila pivote
- Operaciones de fila para actualizar tableau
- Mostrar pasos del proceso completo
- Detectar solución óptima

## Estructura del Proyecto

```
proyecto/
├── core/
│   ├── modelo.py              # Clases base (Variable, Restriccion, Iteracion)
│   ├── parser/
│   │   └── expresion.py       # Parser de expresiones lineales
│   ├── gran_m.py              # Constructor del tableau inicial
│   └── solucionador_simplex.py# Gestor de iteraciones
├── ui/
│   ├── ventana_principal.py   # Ventana principal
│   ├── panel_entrada.py       # Panel de entrada de datos
│   ├── panel_resultado.py     # Visualización del tableau
│   └── formateador_tableau.py # Utilidades de formato
├── main.py
└── README.md
```

## Uso

### Instalación

```bash
python -m pip install -r requirements.txt  # No hay dependencias externas actualmente
```

### Ejecutar

```bash
python main.py
```

### Ejemplo de Uso

1. **Ingresar Función Objetivo**: `2x1 + 3x2`
2. **Seleccionar tipo**: Maximizar o Minimizar
3. **Agregar Restricciones**:
   - `x1 + x2 <= 5` (Restricción 1)
   - `2x1 + x2 <= 8` (Restricción 2)
4. **Presionar "Resolver"**
5. El tableau inicial se mostrará automáticamente

## Ejemplos de Problemas

### Ejemplo 1: Problema Simple (Solo <=)

```
Maximizar: Z = 2x1 + 3x2

Sujeto a:
  x1 + x2 <= 5
  2x1 + x2 <= 8
  x1, x2 >= 0
```

El tableau incluirá variables de holgura S1 y S2.

### Ejemplo 2: Problema con Artificiales

```
Maximizar: Z = 3x1 + 2x2

Sujeto a:
  x1 + x2 >= 4
  2x1 + x2 = 6
  x1, x2 >= 0
```

El tableau incluirá:
- Variable de exceso E1 para restricción >=
- Variables artificiales A1 y A2 para >= y =

## Representación Interna

### Variables

- **Variable de Decisión** (xN): Ingresadas por el usuario
- **Variable de Holgura** (SN): Agregada para restricciones <=
- **Variable de Exceso** (EN): Agregada para restricciones >=
- **Variable Artificial** (AN): Agregada para >= y = con penalización M

### Tableau Simplex

```
     x1    x2   S1   S2    b
Z  -2.00 -3.00  0.00 0.00  0.00
R1  1.00  1.00  1.00 0.00  5.00
R2  2.00  1.00  0.00 1.00  8.00
```

- Primera fila: Función objetivo
- Demás filas: Restricciones
- Última columna: Términos independientes (b)

## Formato de Entrada

### Expresiones

```
2x1 + 3x2      ✓ Válido
-x1 + 5x2      ✓ Válido (coeficiente -1)
x1 - 2x3       ✓ Válido (resta)
4x2            ✓ Válido (una variable)
10             ✗ Inválido (sin variable)
2y1 + x2       ✗ Inválido (variable no reconocida)
```

### Restricciones

```
x1 + x2 <= 5        ✓ Menor o igual
x1 + x2 >= 4        ✓ Mayor o igual
2x1 + x2 = 6        ✓ Igualdad
```

## Arquitectura

### Capas

1. **Capa de Modelos** (`core/modelo.py`)
   - Definición de estructuras de datos
   - Enums para tipos de variables y restricciones

2. **Capa de Parser** (`core/parser/expresion.py`)
   - Análisis de expresiones lineales
   - Conversión a vectores numéricos

3. **Capa de Lógica** (`core/gran_m.py`, `core/solucionador_simplex.py`)
   - Construcción del tableau
   - Gestión de iteraciones

4. **Capa de Presentación** (`ui/`)
   - Interfaz gráfica con Tkinter
   - Formateo y visualización

## Configuración

### Precisión Decimal

Actualmente configurada a **2 decimales** para visualización. Modificable en:
```python
# En ui/formateador_tableau.py
PRECISION = 2
```

### Representación de M

La constante M se representa como un **símbolo literal** "M" en el tableau, no como un valor numérico.

## Próximas Características

- [ ] Algoritmo de pivoteo completo
- [ ] Mostrar pasos de cálculo
- [ ] Detectar degeneración
- [ ] Exportar resultados
- [ ] Historial de iteraciones
- [ ] Gráfico de solución óptima
- [ ] Análisis de sensibilidad
- [ ] Guardar/cargar problemas

## Tecnologías

- **Python 3.13+**
- **Tkinter** (interfaz gráfica)
- Sin dependencias externas

## Autor

Proyecto educativo para curso de Optimización.

## Licencia

MIT
