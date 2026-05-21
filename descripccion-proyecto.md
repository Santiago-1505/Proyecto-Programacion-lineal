# Propósito de la aplicación

La aplicación tendrá como objetivo resolver problemas de programación lineal mediante el método de Gran M utilizando la forma tabular del método simplex.

El usuario podrá ingresar:

- una función objetivo,
- el tipo de optimización (maximizar o minimizar),
- y una cantidad arbitraria de restricciones.

Una vez ingresados todos los datos, el usuario podrá presionar un botón de resolver. Esto generará la primera iteración de la tabla simplex utilizando el método de Gran M.

La aplicación mostrará la tabla correspondiente a cada iteración del algoritmo y permitirá avanzar paso a paso mediante un botón. En cada iteración se actualizarán los valores de la tabla hasta alcanzar la solución óptima del problema. Cuando el problema haya sido resuelto, el botón para avanzar iteraciones será deshabilitado.

---

# Flujo de la aplicación

## Interfaz de entrada

La interfaz tendrá dos puntos principales de entrada de datos.

El primero será la entrada de la función objetivo. Esta se ingresará mediante un campo de texto utilizando una sintaxis similar a:

```text
2x1 + 3x2
```

En esta representación:

- los números a la izquierda de la variable representan los coeficientes,
- y los números a la derecha representan el índice de la variable.

Además, existirán dos radio buttons para seleccionar si el problema será de maximización o minimización.

---

El segundo punto de entrada será una lista dinámica de restricciones.

Cada restricción estará compuesta por:

1. Un campo de texto para el lado izquierdo de la restricción.
2. Un selector desplegable para elegir el tipo de restricción.
3. Un campo de texto para ingresar el lado derecho de la restricción.

Ejemplo:

```text
2x1 + x2 <= 5
```

Los tipos de restricción estarán representados mediante un enum con únicamente tres opciones:

- menor o igual (`<=`)
- mayor o igual (`>=`)
- igualdad (`=`)

---

# Representación interna de expresiones

Las expresiones ingresadas por el usuario serán tokenizadas utilizando objetos de tipo `Termino`.

La clase `Termino` tendrá:

- un coeficiente de tipo entero,
- y una variable de tipo `Variable`.

La clase `Variable` tendrá:

- un índice,
- y un tipo de variable.

Los tipos de variable estarán definidos mediante un enum con cuatro valores:

- Decisión
- Holgura
- Exceso
- Artificial

Todas las variables ingresadas inicialmente por el usuario serán variables de decisión. Las demás variables serán agregadas automáticamente durante la construcción de la primera iteración del método de Gran M.

---

# Parseo y transformación de restricciones

Primero se parseará la función objetivo para determinar la cantidad total de variables de decisión presentes en el problema.

Posteriormente se parsearán las restricciones.

Para cada restricción se creará inicialmente un vector numérico con tamaño igual a la cantidad de variables de decisión y todos sus valores inicializados en cero.

Luego, por cada término presente en la restricción:

- se utilizará el índice de la variable,
- se restará 1 al índice debido a que las variables comienzan desde 1 mientras los vectores comienzan desde 0,
- y se insertará el coeficiente en la posición correspondiente del vector.

Por ejemplo:

```text
2x1 + 5x3
```

se representará internamente como:

```text
[2, 0, 5]
```

Finalmente, cada restricción quedará representada mediante:

- un vector numérico de coeficientes,
- un enum para el tipo de restricción,
- y un entero correspondiente al lado derecho de la restricción.

El lado derecho será ingresado inicialmente como string y convertido posteriormente a entero.

---

# Construcción de la primera iteración (Gran M)

Para construir la primera iteración del método simplex utilizando Gran M, todas las restricciones deberán transformarse en igualdades.

Durante este proceso se recorrerán las restricciones y se irá construyendo dinámicamente la matriz de restricciones.

Cada vez que se agregue una nueva variable de holgura, exceso o artificial:

- se añadirá una nueva columna a la matriz,
- y todas las filas existentes serán extendidas con ceros para mantener dimensiones consistentes.

---

# Conversión de restricciones

## Restricciones menor o igual (`<=`)

A las restricciones de tipo menor o igual se les añadirá una variable de holgura con coeficiente `+1`.

Ejemplo:

```text
x1 + x2 <= 5
```

se transformará en:

```text
x1 + x2 + S1 = 5
```

La variable básica inicial para esta fila será la variable de holgura agregada.

---

## Restricciones mayor o igual (`>=`)

A las restricciones de tipo mayor o igual se les añadirá:

- una variable de exceso con coeficiente `-1`,
- y una variable artificial con coeficiente `+1`.

Ejemplo:

```text
x1 + x2 >= 5
```

se transformará en:

```text
x1 + x2 - E1 + A1 = 5
```

La variable básica inicial para esta fila será la variable artificial.

---

## Restricciones de igualdad (`=`)

A las restricciones de igualdad se les añadirá una variable artificial con coeficiente `+1`.

Ejemplo:

```text
x1 + x2 = 5
```

se transformará en:

```text
x1 + x2 + A1 = 5
```

La variable básica inicial para esta fila será la variable artificial.

---

# Construcción de la función objetivo

La función objetivo también será transformada a su forma tabular.

Para problemas de maximización:

```text
Max Z = 2x1 + 3x2
```

se transformará en:

```text
Z - 2x1 - 3x2 = 0
```

Por lo tanto:

- todos los coeficientes de las variables de decisión cambiarán de signo.

Además, las variables artificiales deberán agregarse a la función objetivo utilizando penalización por M.

Ejemplo:

```text
Z - 2x1 - 3x2 - MA1 - MA2 = 0
```

En el caso de problemas de minimización, los signos deberán manejarse de forma inversa dependiendo de la convención utilizada para la tabla simplex.

---

# Representación de una iteración

Cada iteración del método simplex estará representada mediante una clase `Iteracion`.

Esta clase contendrá:

- la matriz de restricciones,
- la fila correspondiente a la función objetivo,
- el vector de términos independientes,
- y las variables básicas actuales.

Las variables básicas serán necesarias para:

- identificar la base actual,
- mostrar correctamente la tabla,
- y realizar posteriormente las operaciones de pivoteo.

La primera iteración tendrá como variables básicas:

- las variables de holgura agregadas en restricciones `<=`,
- o las variables artificiales agregadas en restricciones `>=` y `=`.
