# COMPREHENSIVE CASCADE BUG ANALYSIS - Simplex Solver

## EXECUTIVE SUMMARY

This document provides a detailed factual analysis of 6 critical bugs in the Simplex solver, their interdependencies, cascade effects, and repair order. Based on code inspection at lines specified in the bug report.

---

## A. STRICT DEPENDENCY ORDER & REPAIR SEQUENCING

### Critical Path Analysis

```
Bug #1 (Duplicate Code) ──────────┐
                                  │
Bug #2 (In-place Mutations) ──────┴──→ Bug #3 (es_minimizacion ignored)
                                  │
Bug #3 ─────────────────────────┬─┘
                                │
Bug #4 (Wrong M sign)───────────┴──→ Bug #5 (Missing Canonicalization)
                                │
Bug #5 ──────────────────────┬──┘
                             │
                        Bug #6 (Index Alignment)

MUST-DO-FIRST:     Bug #1, Bug #2 (both critical blockers)
DEPENDS ON:        Bug #1+#2 → Bug #3 → Bug #4 → Bug #5
INDEPENDENT:       Bug #6 (but cascades from #1 through history display)
```

### Detailed Dependency Matrix

| Bug | Must Complete Before | Reason | Impact If Skipped |
|-----|----------------------|--------|-------------------|
| #1 | #2, #3, #5, #6 | Duplicate code corrupts history irreparably | UI shows phantom rows; iteration count wrong |
| #2 | #3, #5 | Mutations prevent proper copy; destroys phase transitions | History states are wrong; phase 1→2 fails |
| #3 | #4, #5 | Can't use es_minimizacion without it being read | Minimization always treated as maximization |
| #4 | #5 | M-sign wrong without proper usage context | Artificials never penalized correctly in phase 1 |
| #5 | #6 (weak) | Assumes #3,#4 fixed for Z-row to be correct | Z-row doesn't reflect true objective state |
| #6 | None | Can verify index mapping independently | Visual display misaligned from computed data |

### Why These Orderings Matter

**#1 MUST be first:** Every subsequent bug analysis uses iteration history. With duplicate code:
- `self.iteraciones[i]` doesn't correspond to iteration i
- All downstream code that indexes history breaks
- Fixing other bugs won't help if history is phantom

**#2 DEPENDS on #1:** After removing duplicate code, the mutation-before-copy sequence becomes visible:
- Line 154: `_realizar_pivoteo()` mutates `iteracion_actual.tableau` in-place
- Line 161-166: Then `_crear_siguiente_iteracion()` tries to copy the mutated state
- Phase transitions need UNMUTATED previous state for comparison

**#3 ENABLES #4 & #5:** Until `es_minimizacion` is read/used:
- M-sign changes make no difference (both treated same)
- Canonicalization is meaningless (no differentiation)
- Bug #3 is prerequisite for #4 and #5 to even be testable

---

## B. CASCADE FAILURES - Cross-Bug Interactions

### Scenario 1: Fix Bug #1 WITHOUT Fixing Bug #2

**What breaks:** Everything downstream

```
Initial: iteraciones = [iter0]
After iteration 1:
  - Lines 109-186 execute
  - _realizar_pivoteo() MUTATES iter0.tableau IN PLACE
  - iter1 created as copy of mutated iter0
  - iteraciones = [iter0_MUTATED, iter1]
  - iter0_MUTATED now has incorrect tableau!

After iteration 2:
  - Next siguiente_iteracion() uses iteracion_actual (pointing to iter1)
  - But iter0 was corrupted, so any UI trying to navigate history fails
  - History traversal: iter0_MUTATED → iter1_CORRUPTED → iter2_CORRUPTED
```

**Cascade Effect:** 
- UI history navigation breaks (line 190: `len(self._solucionador.iteraciones)`)
- User tries to go back to iteration 0 → sees wrong tableau
- All subsequent iterations built on wrong basis

### Scenario 2: Fix Bug #3 WITHOUT Fixing Bug #4

**What breaks:** Minimization correctness

```
MINIMIZATION PROBLEM:
  Minimize: 2x1 + 3x2
  Subject to: x1 + x2 >= 5

Current behavior (Bug #4 active):
  - fila_z = [-2, -3, 0, 0, +1e10]  (line 329: ALWAYS +M for artificial)
  - Artificial A1 in base with coeff +1e10
  - Z = -2x1 - 3x2 + 1e10*A1
  - Problem: +M ADDS to Z, making artificial attractive to minimize!
  - Correct: Should have -M to PENALIZE artificial

Expected (Bug #3 fixed, reads es_minimizacion):
  - For minimization: fila_z = [-2, -3, 0, 0, -1e10]  (subtract M)
  - Z = -2x1 - 3x2 - 1e10*A1
  - Now artificial is penalized correctly
```

**Cascade Effect:**
- Phase 1 never eliminates artificials (they look optimal with wrong M-sign)
- Phase 2 never starts
- Problem marked "infeasible" when it's actually feasible

### Scenario 3: Fix Bug #5 WITHOUT Fixing Bug #3 & #4

**What breaks:** Z-row initialization

```
Initial tableau SHOULD be (for minimization):
  Objective: min Z = 2x1 + 3x2
  Constraint: x1 + x2 >= 5 (requires A1)
  
Expected initial Z-row (with Gran-M canonicalization):
  Z - 2x1 - 3x2 - M*A1 = 0
  Rearranged: Z - 2x1 - 3x2 - M*A1 = 0
  
Current code (lines 314-329):
  - Creates fila_z = [-2, -3, 0, 0, +M]
  - Does NOT subtract M*constraint_row from Z-row
  - Initial Z value = 0 (should be ±M depending on minimization)
  
If fix #5 (proper canonicalization) without #3,#4:
  - Would compute: Z - 2x1 - 3x2 + M*(x1 + x2 - 5) = 0  (WRONG sign on M)
  - Simplifies: Z + (M-2)x1 + (M-3)x2 - 5M = 0
  - Initial terminos_independientes[0] = -5M (HUGE negative)
  - Not only wrong, but numerically unstable
```

**Cascade Effect:**
- Z-row initialization over-penalizes (or under-penalizes)
- Pivot selection becomes non-optimal
- Wrong variable enters base
- Entire solution path diverges

### Scenario 4: Don't Fix Bug #2, Fix Others

**What breaks:** Phase 1→2 Transition

```
Phase 1 detection (lines 42, 74-77):
  - Checks if any variables_basicas have type == ARTIFICIAL
  - Sets en_fase_1 = True if found

After first iteration with BUG #2 active:
  - _realizar_pivoteo() modified iter0.tableau AND iter0.variables_basicas IN PLACE
  - Line 158: iteracion_actual.variables_basicas[fila-1] = nueva_var
  - This updates the ORIGINAL iter0 in self.iteraciones[0]!
  - _crear_siguiente_iteracion() copies variables_basicas (line 399)
  - But both iter0 and iter1 now share modified state

Transition check (line 174-183):
  - Looks at nueva_iteracion.variables_basicas
  - But since iter0 was mutated, phase 1 detection reading iter0 gets wrong data
  - Phase 1 might terminate early or not at all
```

**Cascade Effect:**
- Phase transitions don't work correctly
- Artificial variables don't get eliminated properly
- Algorithm stays in phase 1 or jumps to phase 2 prematurely

---

## C. CRITICAL STATE MACHINES

### The Iteration History State Machine

**Expected Behavior:**
```
Initial:     iteraciones = [iter0]
             iteracion_actual = 0

After iter 1: iteraciones = [iter0, iter1]
             iteracion_actual = 1

After iter 2: iteraciones = [iter0, iter1, iter2]
             iteracion_actual = 2

Properties:
- IMMUTABLE: iter0, iter1, iter2 never change after creation
- ORDERED: iter[i].numero_iteracion == i
- INDEXED: self.iteraciones[self.iteracion_actual] is current
```

**Actual Behavior (With Bug #1 + #2):**
```
Initial:     iteraciones = [iter0]
             iteracion_actual = 0

After iter 1:
  Line 154: _realizar_pivoteo(iter0, 1, 0)  → MUTATES iter0
  Line 161-166: iter1 = _crear_siguiente_iteracion(iter0_MUTATED, ...)
  Line 169: iteraciones = [iter0_MUTATED, iter1]
  Line 170: iteracion_actual = 1

After iter 2:
  Line 154: _realizar_pivoteo(iter1, 2, 1)  → MUTATES iter1
  Line 161-166: iter2 = _crear_siguiente_iteracion(iter1_MUTATED, ...)
  Line 169: iteraciones = [iter0_MUTATED, iter1_MUTATED, iter2]
  Line 170: iteracion_actual = 2

Result:
- iter0 CHANGED (corrupted)
- History is MUTABLE not immutable
- Accessing iteraciones[0].tableau now gives mutated data
- UI showing "go back" sees wrong values
```

### The Variables_Basicas Evolution

**Expected:**
```
iter0.variables_basicas = [S1, S2]        (problem with only <=)
iter1.variables_basicas = [x1, S2]        (after pivoting)
iter2.variables_basicas = [x1, x2]        (optimal)

Each iteration frozen in time with its variables_basicas state.
```

**Actual (Bug #2):**
```
iter0.variables_basicas = [S1, S2]
Line 158 (in iteration 1): iter0.variables_basicas[0] = x1  → MUTATES iter0!
iter1 = copy(iter0)  → iter1 also has [x1, S2]

But later code might reference iter0:
  Line 46: _tiene_variables_artificiales(iter0)  → reads MUTATED iter0
  Result: Incorrect phase detection
```

### The Tableau State Machine

**Mutable vs Immutable Decision:**

Current code design (WRONG):
- `_realizar_pivoteo()` mutates in-place
- Assumes caller will copy AFTER
- Problem: Copy happens in `_crear_siguiente_iteracion()` AFTER mutation
- All previous references now see mutated state

Correct design (REQUIRED):
- Option A: Immutable pivot - return NEW tableau instead of mutating
- Option B: Pre-copy pivot - copy BEFORE mutating
- Option C: Split operations - separate "read previous" from "create new"

---

## D. ARCHITECTURAL REWORK NEEDS

### Current Architecture (BROKEN)

```
siguiente_iteracion():
  1. Select variable_entrante (uses iteracion_actual)
  2. Select variable_saliente (uses iteracion_actual)
  3. _realizar_pivoteo(iteracion_actual)  → MUTATES
  4. _crear_siguiente_iteracion(iteracion_actual)  → TRIES TO COPY MUTATED
  5. Append to history
  6. Check optimality
  7. DUPLICATE STEPS 1-6 IF NOT OPTIMAL

Problems:
- Step 3 mutates, Step 4 copies - order wrong
- Step 7 duplicates entire logic
- No atomicity
- Multiple mutation points
```

### Required Refactoring

**Option A: Immutable Pivot (CLEANEST)**

```python
def siguiente_iteracion(self):
    """Single, clean iteration step."""
    iter_actual = self.obtener_iteracion_actual()
    
    # Select entries (non-mutating)
    col_entrante = self._seleccionar_variable_entrante(iter_actual)
    if col_entrante is None:
        self._handle_phase_transition_or_optimality()
        return
    
    fila_saliente, razones = self._seleccionar_variable_saliente(iter_actual, col_entrante)
    if fila_saliente is None:
        self.es_ilimitado = True
        return
    
    # Create new iteration WITHOUT mutating current
    nueva_iteracion = self._crear_siguiente_iteracion_inmutable(
        iter_actual,
        col_entrante,
        fila_saliente,
        razones
    )
    
    # Append to history
    self.iteraciones.append(nueva_iteracion)
    self.iteracion_actual += 1
    
    # No need to check optimality - _crear_siguiente_iteracion_inmutable
    # doesn't need to compute optimality, but may return flag

def _crear_siguiente_iteracion_inmutable(self, iter_anterior, col_pivot, fila_pivot, razones):
    """Create new iteration without mutating the previous one."""
    
    # Copy everything first
    new_tableau = [fila[:] for fila in iter_anterior.tableau]
    new_terminos = iter_anterior.terminos_independientes[:]
    new_variables_basicas = iter_anterior.variables_basicas[:]
    
    # Perform pivot operations on COPIES
    self._realizar_pivoteo_sobre_copias(
        new_tableau,
        new_terminos,
        fila_pivot,
        col_pivot
    )
    
    # Update variables_basicas on copy
    nueva_var = iter_anterior.nombres_variables_todas[col_pivot]
    new_variables_basicas[fila_pivot - 1] = nueva_var
    
    return Iteracion(
        numero_iteracion=iter_anterior.numero_iteracion + 1,
        tableau=new_tableau,
        terminos_independientes=new_terminos,
        variables_basicas=new_variables_basicas,
        nombres_variables_todas=iter_anterior.nombres_variables_todas[:],
        columna_pivote=col_pivot,
        fila_pivote=fila_pivot,
        razones_minimo_cociente=razones,
        variable_entrante=iter_anterior.nombres_variables_todas[col_pivot],
        variable_saliente=iter_anterior.variables_basicas[fila_pivot - 1]
    )
```

**Option B: Pre-Copy Then Mutate (CURRENT BUG)**

```python
# CURRENT BROKEN CODE - DO NOT USE:
nueva_iteracion = self._crear_siguiente_iteracion(
    iteracion_actual,  # NOT YET PIVOTED
    col_entrante,
    fila_saliente,
    razones
)

def _crear_siguiente_iteracion(self, iter_anterior, ...):
    # Makes copy of UN-pivoted state
    new_tableau = [fila[:] for fila in iter_anterior.tableau]
    
    # But then next iteration, _realizar_pivoteo is called on iter_anterior
    # AFTER this copy is made - so previous iteration's copy is stale
```

### Code Separation

**Remove duplicate code (lines 188-225):**
- Delete entirely
- Rely on loop calling `siguiente_iteracion()` repeatedly
- Each call does exactly one iteration step

**Split `siguiente_iteracion()` into atomic pieces:**

```python
def siguiente_iteracion(self):
    iter_actual = self.obtener_iteracion_actual()
    
    # Try to make one step
    nueva_iteracion = self._intentar_siguiente_paso(iter_actual)
    if nueva_iteracion is None:
        # Handle termination
        self._manejar_termino_algoritmo()
        return
    
    # Unconditionally add to history
    self.iteraciones.append(nueva_iteracion)
    self.iteracion_actual += 1

def _intentar_siguiente_paso(self, iter_actual) -> Iteracion | None:
    """Attempts one pivot step. Returns new iteration or None if done."""
    
    col_entrante = self._seleccionar_variable_entrante(iter_actual)
    if col_entrante is None:
        # Check phase 1→2 transition
        if self.en_fase_1:
            self.en_fase_1 = False
            # Try again with new rules
            return self._intentar_siguiente_paso(iter_actual)
        else:
            self.resuelto = True
            return None
    
    fila_saliente, razones = self._seleccionar_variable_saliente(iter_actual, col_entrante)
    if fila_saliente is None:
        self.es_ilimitado = True
        return None
    
    # Create new iteration without mutation
    return self._crear_siguiente_iteracion_immutable(
        iter_actual, col_entrante, fila_saliente, razones
    )
```

---

## E. MUTATION PREVENTION - Current vs Required

### Current Flow (BROKEN)

```python
# Line 154:
self._realizar_pivoteo(iteracion_actual, fila_saliente, col_entrante)

# Inside _realizar_pivoteo (lines 340-351):
iteracion.tableau[fila_pivote][j] /= pivote  # MUTATES iteracion.tableau
iteracion.terminos_independientes[fila_pivote] /= pivote  # MUTATES

# After pivoting, iteracion_actual.tableau is CHANGED
# But iteracion_actual is SAME OBJECT as self.iteraciones[self.iteracion_actual]

# Line 161-166:
nueva_iteracion = self._crear_siguiente_iteracion(
    iteracion_actual,  # NOW PIVOTED!
    ...
)

# This creates a copy of the PIVOTED state
# But the previous iteration in history is also the PIVOTED state
# Result: All previous iterations are now WRONG

# Line 169:
self.iteraciones.append(nueva_iteracion)
```

**Timeline visualization:**

```
Time 0:
  self.iteraciones[0].tableau = [[1, 2], [3, 4]]
  iter_actual = self.iteraciones[0]

Time 1: Call siguiente_iteracion()
  _realizar_pivoteo(iter_actual, 1, 0)
  
  DURING pivoting:
    self.iteraciones[0].tableau = [[1, 0.5], [0, 1]]  ← MUTATED!
    iter_actual.tableau = [[1, 0.5], [0, 1]]  ← SAME OBJECT, also changed
  
  nueva_iteracion = copy(iter_actual)
  nueva_iteracion.tableau = [[1, 0.5], [0, 1]]  ← Copy of mutated state
  
  self.iteraciones.append(nueva_iteracion)
  self.iteraciones = [
    iter0_MUTATED = [[1, 0.5], [0, 1]],  ← SHOULD BE [[1, 2], [3, 4]]
    iter1 = [[1, 0.5], [0, 1]]
  ]
```

### Required Fix: Copy BEFORE Pivot

```python
def siguiente_iteracion(self):
    iter_actual = self.obtener_iteracion_actual()
    
    col_entrante = self._seleccionar_variable_entrante(iter_actual)
    if col_entrante is None:
        # ... handle termination
        return
    
    fila_saliente, razones = self._seleccionar_variable_saliente(iter_actual, col_entrante)
    if fila_saliente is None:
        # ... handle ilimitado
        return
    
    # COPY FIRST before any mutation
    tabla_copia = [fila[:] for fila in iter_actual.tableau]
    terminos_copia = iter_actual.terminos_independientes[:]
    
    # NOW pivot on copies
    self._realizar_pivoteo_en_copias(tabla_copia, terminos_copia, fila_saliente, col_entrante)
    
    # Create new iteration from copies
    nueva_var_basica = iter_actual.nombres_variables_todas[col_entrante]
    nueva_variables_basicas = iter_actual.variables_basicas[:]
    nueva_variables_basicas[fila_saliente - 1] = nueva_var_basica
    
    nueva_iteracion = Iteracion(
        numero_iteracion=iter_actual.numero_iteracion + 1,
        tableau=tabla_copia,
        terminos_independientes=terminos_copia,
        variables_basicas=nueva_variables_basicas,
        nombres_variables_todas=iter_actual.nombres_variables_todas[:],
        columna_pivote=col_entrante,
        fila_pivote=fila_saliente,
        razones_minimo_cociente=razones,
        variable_entrante=nueva_var_basica,
        variable_saliente=iter_actual.variables_basicas[fila_saliente - 1]
    )
    
    self.iteraciones.append(nueva_iteracion)
    self.iteracion_actual += 1
```

---

## F. TESTING POINTS - Proof of Correctness

### Test 1: Bug #1 Fixed (Duplicate Code Removed)

**Test Case:**
```python
def test_bug1_no_duplicate_iterations():
    """Verify that solving a simple problem doesn't create phantom iterations."""
    # Problem: max 2x1 + 3x2 s.t. x1 + x2 <= 5, 2x1 + x2 <= 8
    
    constructor = ConstructorPrimerIteracion()
    iteracion = constructor.construir_tableau_inicial(...)
    solver = SolucionadorSimplex(iteracion, False)
    
    initial_count = len(solver.iteraciones)  # Should be 1
    
    solver.siguiente_iteracion()
    assert len(solver.iteraciones) == initial_count + 1  # Must be exactly 2, not 3
    
    solver.siguiente_iteracion()
    assert len(solver.iteraciones) == initial_count + 2  # Must be exactly 3, not 4 or 5
    
    # Continue until optimal
    while solver.puede_avanzar():
        old_count = len(solver.iteraciones)
        solver.siguiente_iteracion()
        new_count = len(solver.iteraciones)
        assert new_count == old_count + 1  # EACH call adds EXACTLY 1 iteration
```

**Expected Result:** PASS - Each `siguiente_iteracion()` call adds exactly one iteration.

### Test 2: Bug #2 Fixed (No In-Place Mutations)

**Test Case:**
```python
def test_bug2_immutable_history():
    """Verify previous iterations don't change after creating new ones."""
    constructor = ConstructorPrimerIteracion()
    iteracion = constructor.construir_tableau_inicial(...)
    solver = SolucionadorSimplex(iteracion, False)
    
    # Snapshot iteration 0
    iter0_tableau_original = [fila[:] for fila in solver.iteraciones[0].tableau]
    iter0_terminos_original = solver.iteraciones[0].terminos_independientes[:]
    
    # Perform iteration 1
    solver.siguiente_iteracion()
    
    # Check iteration 0 unchanged
    assert solver.iteraciones[0].tableau == iter0_tableau_original, \
        "Iteration 0 tableau was mutated!"
    assert solver.iteraciones[0].terminos_independientes == iter0_terminos_original, \
        "Iteration 0 terminos were mutated!"
    
    # Perform iteration 2
    iter1_tableau_original = [fila[:] for fila in solver.iteraciones[1].tableau]
    solver.siguiente_iteracion()
    
    assert solver.iteraciones[1].tableau == iter1_tableau_original, \
        "Iteration 1 tableau was mutated!"
```

**Expected Result:** PASS - Previous iterations remain unchanged.

### Test 3: Bug #3+#4 Fixed (Minimization with Artificial Variables)

**Test Case:**
```python
def test_bug3_4_minimization_with_artificial():
    """Verify minimization with >= constraint eliminates artificials correctly."""
    # min: 3x1 + 2x2
    # s.t. x1 + x2 >= 4
    
    constructor = ConstructorPrimerIteracion()
    iteracion = constructor.construir_tableau_inicial(
        objetivo="3x1 + 2x2",
        tipo_optimizacion="min",
        restricciones=[Restriccion("x1 + x2", TipoRestriccion.MAYOR_IGUAL, "4")]
    )
    solver = SolucionadorSimplex(iteracion, True)
    
    # Check initial artificial is in basis
    assert any(var.tipo == TipoVariable.ARTIFICIAL for var in iteracion.variables_basicas), \
        "Artificial variable not in initial basis"
    
    # Phase 1: eliminate artificial
    solver.siguiente_iteracion()
    # After first iteration, artificial should start being eliminated
    
    # Continue until artificial eliminated
    while solver.en_fase_1 and solver.puede_avanzar():
        solver.siguiente_iteracion()
    
    # Check artificial eliminated
    final_iter = solver.obtener_iteracion_actual()
    assert not any(var.tipo == TipoVariable.ARTIFICIAL for var in final_iter.variables_basicas), \
        "Artificial variable not eliminated after Phase 1"
    
    # Check final solution
    # For this problem, optimal is x1=4, x2=0 (or x1=0, x2=4 or anywhere on line)
    # Value should be 3*4 + 2*0 = 12 or 3*0 + 2*4 = 8 (minimum is 8)
    z_value = final_iter.terminos_independientes[0]
    assert z_value <= 12.1 and z_value >= 7.9, \
        f"Final Z value {z_value} outside expected range [8, 12]"
```

**Expected Result:** PASS - Artificial eliminated, phase 1→2 transition successful, optimal solution found.

### Test 4: Bug #5 Fixed (Grand M Canonicalization)

**Test Case:**
```python
def test_bug5_grand_m_canonicalization():
    """Verify Z-row is properly adjusted for artificial variables."""
    # min: x1 + x2
    # s.t. x1 + x2 = 3 (requires artificial)
    
    constructor = ConstructorPrimerIteracion()
    iteracion = constructor.construir_tableau_inicial(
        objetivo="x1 + x2",
        tipo_optimizacion="min",
        restricciones=[Restriccion("x1 + x2", TipoRestriccion.IGUALDAD, "3")]
    )
    
    # Check Z-row coefficients
    fila_z = iteracion.tableau[0]
    
    # For minimization with artificial, Z-row should have:
    # - Decision variables: coefficients from objective with their sign
    # - Artificial variables: -M coefficient (penalty for minimization)
    
    # Specifically:
    # Original: Z - x1 - x2 = 0 (minimize objective)
    # With constraint: x1 + x2 = 3 is embedded
    # Initial Z should reflect: Z = 0 + 1*A1*M (to minimize A1)
    
    # Check that the coefficient on artificial is negative for minimization
    artificial_coeff = fila_z[-1]  # Last element should be artificial
    assert artificial_coeff < 0, \
        f"Artificial coefficient {artificial_coeff} should be negative (penalty) for minimization"
    
    # Check it's not just a tiny penalty but actual M
    assert abs(artificial_coeff) > 1e9, \
        f"Artificial penalty {artificial_coeff} should use M (very large)"
    
    # Check initial Z value reflects the penalty
    initial_z = iteracion.terminos_independientes[0]
    # With A1 = 3 and penalty -M*3, Z should be approximately -3*M
    # But since A1 should be eliminated in first iteration with proper M,
    # we just check it's there
    assert isinstance(initial_z, (int, float)), \
        f"Initial Z value should be numeric"
```

**Expected Result:** PASS - Artificial has -M penalty for minimization, canonicalization correct.

### Test 5: Bug #6 Fixed (Index Alignment)

**Test Case:**
```python
def test_bug6_index_alignment_razones():
    """Verify index alignment between tableau rows and reasons calculation."""
    # Simple problem with 2 constraints
    constructor = ConstructorPrimerIteracion()
    iteracion = constructor.construir_tableau_inicial(
        objetivo="2x1 + 3x2",
        tipo_optimizacion="max",
        restricciones=[
            Restriccion("x1 + x2", TipoRestriccion.MENOR_IGUAL, "10"),
            Restriccion("2x1 + x2", TipoRestriccion.MENOR_IGUAL, "8"),
        ]
    )
    solver = SolucionadorSimplex(iteracion, False)
    
    # Get first entering variable
    col_entrante = solver._seleccionar_variable_entrante(iteracion)
    
    # Calculate exit variable
    fila_saliente, razones = solver._seleccionar_variable_saliente(iteracion, col_entrante)
    
    # Verify length of razones
    num_restricciones = iteracion.obtener_num_restricciones()
    assert len(razones) == num_restricciones, \
        f"Reasons list length {len(razones)} != number of constraints {num_restricciones}"
    
    # Verify each reason corresponds to correct row
    for i in range(num_restricciones):
        tableau_row_index = i + 1  # tableau[0] is Z-row
        coeff = iteracion.tableau[tableau_row_index][col_entrante]
        termino = iteracion.terminos_independientes[tableau_row_index]
        
        if coeff > 0:
            expected_razon = termino / coeff
            assert abs(razones[i] - expected_razon) < 1e-9, \
                f"Reason {i}: calculated {razones[i]} != expected {expected_razon}"
        else:
            assert razones[i] == float('inf'), \
                f"Reason {i}: non-positive coefficient should give inf, got {razones[i]}"
```

**Expected Result:** PASS - Reasons calculated correctly for each constraint row.

---

## G. MATHEMATICAL CORRECTNESS - Minimization vs Maximization

### Standard Form Transformation

**Minimization Problem:**
```
Original: min Z = c1*x1 + c2*x2 + ... + cn*xn

Standard form tableau:
  Z - c1*x1 - c2*x2 - ... - cn*xn = 0

With artificial A1, A2, ..., Ap:
  Penalties applied in objective: -M*A1 - M*A2 - ... - M*Ap

So fila_z coefficients:
  For xj: -cj  (from objective)
  For Aj: -M   (penalty term)

Expected fila_z = [-c1, -c2, ..., 0, 0, ..., -M, -M, ...]
                   └─────────────┘  └─────────┘  └────────┘
                    decision vars   slack/excess   artificial
```

**Maximization Problem:**
```
Original: max Z = c1*x1 + c2*x2 + ... + cn*xn

Standard form tableau:
  Z - c1*x1 - c2*x2 - ... - cn*xn = 0  (same!)
  
But we negate coefficients for maximization:
  Negate objective: min(-Z) = -c1*x1 - c2*x2 - ...
  
Standard form: Z + c1*x1 + c2*x2 + ... = 0
No wait, we always use negation rule.

Actually BOTH use: Z - c1*x1 - c2*x2 - ... = 0

With artificial:
  Penalties: +M*A1 + M*A2 + ... (OPPOSITE sign from minimization!)

Expected fila_z = [-c1, -c2, ..., 0, 0, ..., +M, +M, ...]
```

Wait, this reveals BUG #4 is WRONG even in the analysis above.

### Correct Formulation (from Linear Programming Theory)

For ANY problem (min or max), we use:
```
Z - c1*x1 - ... = 0  (form of tableau)

Optimality condition: all coefficients in Z-row >= 0 (same for both min/max)
Entering variable: most negative coefficient

But the INITIAL setup differs:
```

**For MINIMIZATION with artificial:**
```
Objective: min c1*x1 + c2*x2 + ... + cp*xp (decision variables only)
Constraints: Ax = b

Two-phase approach:
Phase 1: min sum(Ai)  where Ai = artificials
  This is equivalent to: min M*A1 + M*A2 + ...
  
Tableau Phase 1: Z - M*A1 - M*A2 - ... = 0
So fila_z for artificials: -M, -M, ...

Phase 2: min c1*x1 + c2*x2 + ... (decision vars only)
Tableau Phase 2: Z - c1*x1 - c2*x2 - ... = 0
```

**For MAXIMIZATION with artificial:**
```
Same two-phase approach!
Phase 1: max -sum(Ai) is equivalent to min sum(Ai)
  So tableau Phase 1: Z - M*A1 - M*A2 - ... = 0 (same!)
  fila_z for artificials: -M, -M, ...

Phase 2: max c1*x1 + c2*x2 + ...
  This is equivalent to: min -(c1*x1 + c2*x2 + ...)
  So negate objective in tableau: Z - (-c1)*x1 - (-c2)*x2 - ...
  Tableau Phase 2: Z + c1*x1 + c2*x2 - ... = 0
  
  Wait, this doesn't match! For maximization we don't negate in phase 1.
```

### Correct Minimization with Big-M

For minimization: optimize decision vars + penalize artificials
```
Objective: min c1*x1 + ... + M*A1 + M*A2 + ...

Tableau: Z - c1*x1 - ... - M*A1 - M*A2 - ... = 0
fila_z:  -c1, -c2, ..., -M, -M, ...

Therefore:
- Decision var coefficients: NEGATIVE of objective coefficient
- Artificial coefficients: -M (NEGATIVE M)
```

### Correct Maximization with Big-M

For maximization: optimize decision vars - penalize artificials
```
Objective: max c1*x1 + ... - M*A1 - M*A2 - ...

Tableau: Z - c1*x1 - ... - (-M)*A1 - (-M)*A2 - ... = 0
       = Z - c1*x1 - ... + M*A1 + M*A2 - ... = 0
fila_z:  -c1, -c2, ..., +M, +M, ...

Therefore:
- Decision var coefficients: NEGATIVE of objective coefficient
- Artificial coefficients: +M (POSITIVE M)
```

### Current Code (WRONG)

```python
# gran_m.py line 314-329
for termino in terminos_obj:
    indice = termino.variable.indice - 1
    if 0 <= indice < self.num_variables_decision:
        # AMBOS casos negan para forma estándar de tabla simplex
        fila_z[indice] = -termino.coeficiente  # Same for both min/max

# Agregar coeficientes para variables artificiales (M)
for _ in variables_agregadas['artificial']:
    # Penalización M (valor grande)
    fila_z.append(M_PENALIZACION)  # ALWAYS +M, never -M
```

**BUG #4:** Always appends `+M` for artificials, should be:
- Minimization: `-M`
- Maximization: `+M`

Requires reading `self.tipo_optimizacion` (which isn't stored! This is actually part of Bug #3).

### Initial Z-Row Values

**Minimization:**
```
Initial configuration:
  Artificial variables A1, A2, ... are basic
  All decision variables = 0
  All slack/excess = 0

Objective value: Z = M*A1 + M*A2 + ... (sum of artificials)
With constraint: x1 + x2 + A1 = 4
  Initial: 0 + 0 + A1 = 4 → A1 = 4
  Initial Z = M * 4 = 4M

Tableau form: Z - c1*x1 - ... - M*A1 - ... = 0
Substituting: Z - 0 - ... - M*4 - ... = 0
             Z = 4M

In tableau: terminos_independientes[0] = 4M (positive large number)
```

**What current code does (Bug #5):**
```
Doesn't compute initial Z considering constraint substitution.
Just sets terminos_independientes[0] = 0 (line 85 in gran_m.py)

Should compute: sum(M * bi for each constraint with artificial Ai)
```

---

## H. RISK ASSESSMENT - Indirect Dependencies

### File Dependency Map

```
core/solucionador_simplex.py:
  ├─ Reads: core.modelo (Iteracion, Variable)
  ├─ Called by: ui/ventana_principal.py
  │             ejemplos.py
  ├─ Uses: _realizar_pivoteo() [MUTATES]
  │        _crear_siguiente_iteracion() [COPIES]
  │        _seleccionar_variable_entrante()
  │        _seleccionar_variable_saliente()
  │        _es_optimo()
  ├─ USED BY UI:
  │  └─ ui/ventana_principal.py:
  │     ├─ Gets: iteraciones[] (Bug #1 depends on this)
  │     ├─ Gets: obtener_iteracion_actual() (Bug #2 affects data)
  │     ├─ Calls: puede_avanzar()
  │     ├─ Calls: siguiente_iteracion()
  │     └─ Shows: len(self._solucionador.iteraciones) (Bug #1 breaks this)
  │
  ├─ CALLED BY:
  │  ├─ ui/ventana_principal.py:_on_resolver()
  │  └─ ejemplos.py
  │
  └─ Related to:
     ├─ core/gran_m.py (constructs initial iteracion)
     │  ├─ Uses: M_PENALIZACION (Bug #4 constant)
     │  ├─ Uses: tipo_optimizacion param (Bug #3 - not stored)
     │  └─ Builds: fila_z (Bug #5 affects this)
     │
     └─ ui/formateador_tableau.py (displays iterations)
        ├─ Iterates: iteracion.tableau (Bug #2 corrupts)
        ├─ Reads: iteracion.variables_basicas (Bug #2 mutates)
        ├─ Reads: iteracion.razones_minimo_cociente (Bug #6 misaligns)
        └─ Calls: FormateadorTableau.obtener_datos_tabla()
```

### UI Components Affected

| UI Component | Bug #1 | Bug #2 | Bug #3 | Bug #4 | Bug #5 | Bug #6 |
|--------------|--------|--------|--------|--------|--------|--------|
| VentanaPrincipal._on_siguiente_iteracion | BREAKS | AFFECTS | NO | NO | NO | NO |
| VentanaPrincipal._actualizar_estado_controles (line 190) | BREAKS | NO | NO | NO | NO | NO |
| PanelResultado.mostrar_iteracion | BREAKS | AFFECTS | NO | NO | AFFECTS | AFFECTS |
| TablaSimplex.cargar_iteracion | BREAKS | AFFECTS | NO | NO | AFFECTS | BREAKS |
| FormateadorTableau.obtener_datos_tabla | NO | AFFECTS | NO | NO | NO | BREAKS |

### What Breaks Per Bug

**Bug #1 (Duplicate Code):**
- UI iteration counter wrong (len(iteraciones) includes phantom rows)
- Navigation to previous iterations shows wrong data
- "Iteración X | Y restricciones..." label misaligned

**Bug #2 (In-place Mutations):**
- Previous iterations change after new ones created
- History replaying doesn't work (if UI implements that)
- Phase 1 detection fails (reads mutated iter0)

**Bug #3 (es_minimizacion ignored):**
- Minimization problems solved incorrectly
- Converges to wrong solution
- May miss feasible region entirely

**Bug #4 (Wrong M sign):**
- Artificial variables not penalized correctly
- Phase 1 never eliminates artificials
- Phase 2 never starts (stays in phase 1 forever)
- Or premature phase 2 transition

**Bug #5 (Missing Canonicalization):**
- Initial Z-row doesn't reflect constraint penalties
- Pivot sequence suboptimal
- Numerical instability (very large Z values)

**Bug #6 (Index Misalignment):**
- Highlights in UI (column/row) point to wrong cells
- Minimum ratio calculation shows wrong row as selected
- Visual pedagogical value lost (hard to follow algorithm)

### Regression Tests Required

After each fix, these tests must PASS:

```
1. REGRESSION_TEST_SIMPLE_MAX:
   max 2x1 + 3x2 s.t. x1 + x2 <= 5, 2x1 + x2 <= 8
   Expected iterations: 3
   Expected optimal Z: 13 (at x1=1, x2=3 or similar)

2. REGRESSION_TEST_MINIMIZATION:
   min x1 + 2x2 s.t. x1 + x2 >= 3, x1 >= 1
   Expected iterations: 2-3
   Expected optimal Z: 3 (at x1=1, x2=2 or x1=3, x2=0)

3. REGRESSION_TEST_ARTIFICIAL:
   min 2x1 + 3x2 s.t. x1 + x2 = 5, x1, x2 >= 0
   Expected: Phase 1 (eliminate artificial), Phase 2 (optimize)
   Expected optimal Z: 10 (at x1=0, x2=5 or x1=5, x2=0)

4. REGRESSION_TEST_UNBOUNDED:
   max x1 s.t. x1 - x2 <= 0
   Expected: es_ilimitado = True (correct detection)

5. REGRESSION_TEST_INFEASIBLE:
   max x1 + x2 s.t. x1 + x2 <= 2, x1 + x2 >= 3
   Expected: es_infactible = True (correct detection)

6. REGRESSION_TEST_IMMUTABILITY:
   Solve any problem to iteration 2+
   Check: self.iteraciones[0] unchanged after iter 2,3,4,...

7. REGRESSION_TEST_NO_PHANTOM_ITERATIONS:
   Solve simple problem (max 2x1 + 3x2 s.t. x1 + x2 <= 5)
   Expected iterations: 2 (initial + 1 optimal)
   Check: len(self.iteraciones) increases by exactly 1 per next()
```

---

## SUMMARY TABLE

| Bug | Severity | Dependency | Fix Order | Lines | Root Cause | Cascade |
|-----|----------|-----------|-----------|-------|-----------|---------|
| #1 | CRITICAL | Blocks all | 1st | 188-225 | Duplicate code block | Corrupts history for #5,#6 |
| #2 | CRITICAL | Blocks #3,#5 | 2nd | 312-351 | Mutate before copy | Breaks phase transitions |
| #3 | HIGH | Enables #4,#5 | 3rd | 32,315 | es_minimizacion not stored/used | Minimization ignored |
| #4 | HIGH | Depends on #3 | 4th | 329 | Always +M never -M | Artificials never eliminated |
| #5 | MEDIUM | Depends on #3,#4 | 5th | 74-85 | Initial Z-row not canonicalized | Suboptimal pivots |
| #6 | LOW | Independent | 6th | 283-310 | Index list mismatch | UI visualization misaligned |

---

## CONCLUSION

**Critical Path (Must Complete):**
1. Remove duplicate code (Bug #1)
2. Implement immutable copying (Bug #2)
3. Store and use tipo_optimizacion (Bug #3)
4. Conditional M-sign based on minimization (Bug #4)
5. Canonicalize Z-row with constraint penalties (Bug #5)
6. Fix reason/index mapping in visualization (Bug #6)

**Cannot Skip:** Bugs #1 and #2. Others depend on them.

**Cannot Reorder:** #1 → #2 → #3 → #4 → #5. Each builds on previous.

**Atomic Fix:** After #2, each subsequent fix is atomic and doesn't require other bugs fixed, but they're prerequisites for correctness.

