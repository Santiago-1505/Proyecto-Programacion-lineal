"""
Módulo para construir la primera iteración del método simplex usando Gran M.

Responsable de:
1. Transformar restricciones en igualdades (agregando variables holgura/exceso/artificial)
2. Construir el tableau inicial
3. Manejar variables artificiales con penalización M
"""

from core.modelo import (
    Restriccion, TipoRestriccion, Variable, TipoVariable,
    Termino, Iteracion
)
from core.parser.expresion import (
    parsear_terminos, vectorizar_expresion, obtener_max_indice_variable
)

# Constante M para penalización de variables artificiales
# Usar valor muy grande para asegurar que se eliminen de la base
M_PENALIZACION = 1e10


class ConstructorPrimerIteracion:
    """Construye la primera iteración del tableau simplex con método Gran M."""
    
    def __init__(self):
        self.contador_holgura = 0
        self.contador_exceso = 0
        self.contador_artificial = 0
        self.num_variables_decision = 0
    
    def construir_tableau_inicial(
        self,
        objetivo: str,
        tipo_optimizacion: str,
        restricciones: list[Restriccion]
    ) -> Iteracion:
        """
        Construye la primera iteración del tableau simplex.
        
        Args:
            objetivo: Expresión de la función objetivo (ej: "2x1 + 3x2")
            tipo_optimizacion: "min" o "max"
            restricciones: Lista de objetos Restriccion
        
        Returns:
            Objeto Iteracion con el tableau inicial
        
        Raises:
            ValueError: Si hay problemas con los datos de entrada
        """
        # Resetear contadores
        self.contador_holgura = 0
        self.contador_exceso = 0
        self.contador_artificial = 0
        
        # Determinar cantidad de variables de decisión
        self.num_variables_decision = self._determinar_num_variables_decision(
            objetivo, restricciones
        )
        
        # Validar que haya al menos una restricción
        if not restricciones:
            raise ValueError("Debe haber al menos una restricción")
        
        # Transformar restricciones y construir matriz
        (
            matriz_restricciones,
            variables_basicas,
            terminos_ind,
            variables_agregadas
        ) = self._transformar_restricciones(restricciones)
        
        # Construir fila de función objetivo
        fila_z = self._construir_fila_objetivo(
            objetivo,
            tipo_optimizacion,
            variables_agregadas
        )
        
        # Combinar tableau: fila Z + matriz de restricciones
        tableau = [fila_z] + matriz_restricciones
        
        # El término independiente para Z es siempre 0 (en la forma Z - ... = 0)
        terminos_ind_completo = [0.0] + terminos_ind
        
        # Construir lista completa de todas las variables en orden
        nombres_variables = self._construir_lista_variables_todas()
        
        # Crear objeto Iteracion
        iteracion = Iteracion(
            numero_iteracion=1,
            tableau=tableau,
            variables_basicas=variables_basicas,
            terminos_independientes=terminos_ind_completo,
            nombres_variables_todas=nombres_variables
        )
        
        return iteracion
    
    def _determinar_num_variables_decision(
        self,
        objetivo: str,
        restricciones: list[Restriccion]
    ) -> int:
        """
        Determina el número de variables de decisión del problema.
        
        Analiza tanto la función objetivo como las restricciones.
        """
        max_indice = obtener_max_indice_variable(objetivo)
        
        for restriccion in restricciones:
            max_indice = max(
                max_indice,
                obtener_max_indice_variable(restriccion.lado_izquierdo)
            )
        
        if max_indice == 0:
            raise ValueError("No se encontraron variables de decisión (xN)")
        
        return max_indice
    
    def _transformar_restricciones(
        self,
        restricciones: list[Restriccion]
    ) -> tuple:
        """
        Transforma restricciones en igualdades y construye matriz ampliada.
        
        Returns:
            (matriz_restricciones, variables_basicas, terminos_ind, variables_agregadas)
            
            - matriz_restricciones: list[list[float]] - cada fila es una restricción
            - variables_basicas: list[Variable] - variable básica de cada fila
            - terminos_ind: list[float] - lado derecho de cada restricción
            - variables_agregadas: dict con info de variables agregadas
        """
        # Paso 1: Procesar cada restricción para determinar variables agregadas
        datos_restricciones = []
        
        for restriccion in restricciones:
            # Convertir lado izquierdo a vector
            vector_fila = vectorizar_expresion(
                restriccion.lado_izquierdo,
                self.num_variables_decision
            )
            
            # Convertir lado derecho a número
            try:
                lado_derecho = float(restriccion.lado_derecho)
            except ValueError:
                raise ValueError(
                    f"Lado derecho de restricción debe ser numérico: {restriccion.lado_derecho}"
                )
            
            # Si lado derecho es negativo, multiplicar fila por -1 y cambiar tipo
            if lado_derecho < 0:
                vector_fila = [-x for x in vector_fila]
                lado_derecho = -lado_derecho
                tipo_restriccion = restriccion.tipo
                if tipo_restriccion == TipoRestriccion.MAYOR_IGUAL:
                    tipo_restriccion = TipoRestriccion.MENOR_IGUAL
                elif tipo_restriccion == TipoRestriccion.MENOR_IGUAL:
                    tipo_restriccion = TipoRestriccion.MAYOR_IGUAL
                # IGUALDAD permanece IGUALDAD
            else:
                tipo_restriccion = restriccion.tipo
            
            datos_restricciones.append({
                'vector': vector_fila,
                'lado_derecho': lado_derecho,
                'tipo': tipo_restriccion
            })
        
        # Paso 2: Contar variables a agregar
        for datos in datos_restricciones:
            tipo = datos['tipo']
            if tipo == TipoRestriccion.MENOR_IGUAL:
                self.contador_holgura += 1
            elif tipo == TipoRestriccion.MAYOR_IGUAL:
                self.contador_exceso += 1
                self.contador_artificial += 1
            elif tipo == TipoRestriccion.IGUALDAD:
                self.contador_artificial += 1
        
        # Paso 3: Construir variables básicas iniciales
        variables_basicas = []
        contador_holgura_actual = 0
        contador_exceso_actual = 0
        contador_artificial_actual = 0
        
        for datos in datos_restricciones:
            tipo = datos['tipo']
            var_basica: Variable | None = None
            
            if tipo == TipoRestriccion.MENOR_IGUAL:
                contador_holgura_actual += 1
                var_basica = Variable(TipoVariable.HOLGURA, contador_holgura_actual)
            elif tipo == TipoRestriccion.MAYOR_IGUAL:
                contador_exceso_actual += 1
                contador_artificial_actual += 1
                var_basica = Variable(TipoVariable.ARTIFICIAL, contador_artificial_actual)
            elif tipo == TipoRestriccion.IGUALDAD:
                contador_artificial_actual += 1
                var_basica = Variable(TipoVariable.ARTIFICIAL, contador_artificial_actual)
            else:
                raise ValueError(f"Tipo de restricción desconocido: {tipo}")
            
            if var_basica is not None:
                variables_basicas.append(var_basica)
        
        # Paso 4: Construir información de variables agregadas para fila Z
        variables_agregadas = {
            'holgura': [Variable(TipoVariable.HOLGURA, i) for i in range(1, self.contador_holgura + 1)],
            'exceso': [Variable(TipoVariable.EXCESO, i) for i in range(1, self.contador_exceso + 1)],
            'artificial': [Variable(TipoVariable.ARTIFICIAL, i) for i in range(1, self.contador_artificial + 1)]
        }
        
        # Paso 5: Construir matriz con todas las columnas
        # Orden: [x1...xn | S1...Sm | E1...Ek | A1...Ap]
        matriz = []
        terminos_ind = []
        
        # Para cada restricción original
        for i, datos in enumerate(datos_restricciones):
            fila = datos['vector'].copy()  # Coeficientes de variables de decisión
            tipo = datos['tipo']
            
            # Agregar columnas para variables de holgura
            # Para cada posición de holgura: 1 si es la holgura de esta restricción, 0 en otro caso
            for j in range(1, self.contador_holgura + 1):
                # Contar cuántas restricciones <= hay antes de la actual
                num_menores_antes = sum(
                    1 for d in datos_restricciones[:i]
                    if d['tipo'] == TipoRestriccion.MENOR_IGUAL
                )
                # ¿Es esta restricción una <= y es la j-ésima <?
                if tipo == TipoRestriccion.MENOR_IGUAL and j == num_menores_antes + 1:
                    fila.append(1.0)
                else:
                    fila.append(0.0)
            
            # Agregar columnas para variables de exceso
            for j in range(1, self.contador_exceso + 1):
                # Contar cuántas restricciones >= hay antes de la actual
                num_mayores_antes = sum(
                    1 for d in datos_restricciones[:i]
                    if d['tipo'] == TipoRestriccion.MAYOR_IGUAL
                )
                # ¿Es esta restricción una >= y es la j-ésima >=?
                if tipo == TipoRestriccion.MAYOR_IGUAL and j == num_mayores_antes + 1:
                    fila.append(-1.0)  # Coeficiente -1 para exceso
                else:
                    fila.append(0.0)
            
            # Agregar columnas para variables artificiales
            # Contar artificiales: primero los de >= , luego los de =
            contador_artificial_antes = sum(
                1 for d in datos_restricciones[:i]
                if d['tipo'] in (TipoRestriccion.MAYOR_IGUAL, TipoRestriccion.IGUALDAD)
            )
            
            for j in range(1, self.contador_artificial + 1):
                if tipo == TipoRestriccion.MAYOR_IGUAL:
                    # Artificial de >=: ¿es la j-ésima?
                    if j == contador_artificial_antes + 1:
                        fila.append(1.0)
                    else:
                        fila.append(0.0)
                elif tipo == TipoRestriccion.IGUALDAD:
                    # Artificial de =: ¿es la j-ésima?
                    if j == contador_artificial_antes + 1:
                        fila.append(1.0)
                    else:
                        fila.append(0.0)
                else:  # MENOR_IGUAL
                    fila.append(0.0)
            
            matriz.append(fila)
            terminos_ind.append(datos['lado_derecho'])
        
        return matriz, variables_basicas, terminos_ind, variables_agregadas
    
    def _construir_fila_objetivo(
        self,
        objetivo: str,
        tipo_optimizacion: str,
        variables_agregadas: dict
    ) -> list:
        """
        Construye la fila Z del tableau.
        
        Para maximización: Z - c1*x1 - c2*x2 - ... - M*A_i - ... = 0
        Para minimización: Z + c1*x1 + c2*x2 + ... + M*A_i + ... = 0
        
        Args:
            objetivo: Expresión de la función objetivo
            tipo_optimizacion: "max" o "min"
            variables_agregadas: Dict con variables artificiales agregadas
        
        Returns:
            Fila Z con todas las columnas (floats numéricos)
        """
        # Parsear objetivo
        terminos_obj = parsear_terminos(objetivo)
        
        # Inicializar vector Z con coeficientes de variables de decisión
        fila_z: list = [0.0] * self.num_variables_decision
        
        for termino in terminos_obj:
            indice = termino.variable.indice - 1
            if 0 <= indice < self.num_variables_decision:
                # AMBOS casos negan para forma estándar de tabla simplex
                fila_z[indice] = -termino.coeficiente
        
        # Agregar coeficientes para variables de holgura (0)
        for _ in variables_agregadas['holgura']:
            fila_z.append(0.0)
        
        # Agregar coeficientes para variables de exceso (0)
        for _ in variables_agregadas['exceso']:
            fila_z.append(0.0)
        
        # Agregar coeficientes para variables artificiales (M)
        # Usar valor numérico para M
        for _ in variables_agregadas['artificial']:
            # Penalización M (valor grande)
            fila_z.append(M_PENALIZACION)
        
        return fila_z
    
    def _construir_lista_variables_todas(self) -> list[Variable]:
        """
        Construye lista ordenada de todas las variables en el tableau.
        
        Orden: [x1, x2, ..., S1, S2, ..., E1, E2, ..., A1, A2, ...]
        """
        variables = []
        
        # Variables de decisión
        for i in range(1, self.num_variables_decision + 1):
            variables.append(Variable(TipoVariable.DECISION, i))
        
        # Variables de holgura
        for i in range(1, self.contador_holgura + 1):
            variables.append(Variable(TipoVariable.HOLGURA, i))
        
        # Variables de exceso
        for i in range(1, self.contador_exceso + 1):
            variables.append(Variable(TipoVariable.EXCESO, i))
        
        # Variables artificiales
        for i in range(1, self.contador_artificial + 1):
            variables.append(Variable(TipoVariable.ARTIFICIAL, i))
        
        return variables
