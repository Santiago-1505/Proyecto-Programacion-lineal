# BUG QUICK REFERENCE - Lookup Tables & Checklists

## A. Line-by-Line Reference

| Bug | File | Lines | What's Wrong | Why | Fix |
|-----|------|-------|--------------|-----|-----|
| #1 | solucionador_simplex.py | 188-225 | EXACT DUPLICATE of 109-186 | Copy-paste error | DELETE lines 188-225 |
| #2a | solucionador_simplex.py | 154 | `_realizar_pivoteo()` called BEFORE copy | Mutates original | Move after creating new iter |
| #2b | solucionador_simplex.py | 161 | Copy happens AFTER mutation | Too late | Copy BEFORE any mutation |
| #3 | solucionador_simplex.py | 32 | Stores but never reads | Not used | Use in Bug #4 decision |
| #4 | gran_m.py | 329 | Always `M_PENALIZACION`, never `-M` | No differentiation | Conditional on `es_minimizacion` |
| #5 | gran_m.py | 85 | Initial Z = 0 | Ignores constraint penalties | Compute: sum(M*b_i for artificial rows) |
| #6 | solucionador_simplex.py | 283-310 | List index off by 1 with tableau | Index mismatch | Verify alignment: reasons[i] ↔ tableau[i+1] |

---

## B. Test Strategy Matrix

| Bug | Test Input | Expected Output | Current Output | Proof |
|-----|-----------|-----------------|-----------------|-------|
| #1 | max 2x1+3x2 s.t. x1+x2≤5, 2x1+x2≤8 | len(iteraciones)=2 | len(iteraciones)=3 | `assert len(s.iteraciones) == 2` |
| #2 | Same, check iter0 after iter1 | tableau[0] unchanged | tableau[0] mutated | `assert s.iteraciones[0].tableau == saved` |
| #3 | min 3x1+2x2 s.t. x1+x2≥4 | optimal solution | wrong solution | `assert z_value == 8` (not infinity/unbounded) |
| #4 | Same with artificial | Phase1→Phase2 transition | stays in Phase1 forever | `assert not s.en_fase_1` (after few iters) |
| #5 | min x1+x2 s.t. x1+x2=3 | terminos[0] ≈ -3M | terminos[0] = 0 | `assert abs(terminos[0]) > 1e9` |
| #6 | Any problem with constraints | len(razones) = num_restricciones | Off-by-one error | `assert len(razones) == iteracion.obtener_num_restricciones()` |

---

## C. Dependency Resolution

### "Can I fix Bug X without Bug Y?"

| X → Y | #1 | #2 | #3 | #4 | #5 | #6 |
|-------|----|----|----|----|----|----|
| **#1→** | — | NO | NO | NO | NO | NO |
| **#2→** | YES | — | NO | NO | NO | NO |
| **#3→** | YES | YES | — | NO | NO | NO |
| **#4→** | YES | YES | YES | — | NO | MAYBE |
| **#5→** | YES | YES | YES | YES | — | YES |
| **#6→** | YES | YES | YES | YES | YES | — |

**Legend:** NO = Previous bug must be fixed first | YES = Can be independent | MAYBE = Works but not optimal

---

## D. Cascade Failure Checklist

### If you skip fixing Bug #1:
- [ ] History shows phantom iterations (double count)
- [ ] UI shows iteration 2 when only 1 completed
- [ ] Previous iterations corrupted by later mutations
- [ ] Cannot navigate history reliably

### If you skip fixing Bug #2 after #1:
- [ ] Phase transitions fail (artificial never leaves base)
- [ ] Previous iterations mutate during algorithm
- [ ] History data is garbage
- [ ] Artificials added to later iterations (wrong)

### If you skip fixing Bug #3 after #1+#2:
- [ ] Minimization treated as maximization
- [ ] Optimal points wrong for min problems
- [ ] Cannot differentiate min vs max

### If you skip fixing Bug #4 after #1+#2+#3:
- [ ] Artificial variables penalized wrong direction
- [ ] Phase 1 never eliminates them (or too fast)
- [ ] Phase 2 never starts (or premature)
- [ ] Algorithm doesn't converge

### If you skip fixing Bug #5 after #1+#2+#3+#4:
- [ ] Initial Z-row incorrect
- [ ] Pivot sequence suboptimal
- [ ] Numerical instability (huge values)
- [ ] Solution path diverges

### If you skip fixing Bug #6:
- [ ] UI visualization confusing
- [ ] Highlights point to wrong rows
- [ ] Mathematical correctness OK, but UI wrong

---

## E. Code Patterns to Look For

### Pattern: "Am I using the variable?"

```python
# Bug #3 Pattern - Variable stored but never used
def __init__(self, iteracion_inicial, es_minimizacion):
    self.es_minimizacion = es_minimizacion  # ← Stored
    # ...
    # Nowhere does it actually READ self.es_minimizacion
    # Search: grep -n "self.es_minimizacion" solucionador_simplex.py
    # Result: Only 1 hit (line 32)
```

### Pattern: "Am I copying before mutating?"

```python
# Bug #2 Pattern - Wrong order
def siguiente_iteracion(self):
    iter_actual = self.obtener_iteracion_actual()
    # ...
    self._realizar_pivoteo(iter_actual, ...)  # ← MUTATES
    nueva_iteracion = self._crear_siguiente_iteracion(
        iter_actual,  # ← Already mutated!
        ...
    )
```

### Pattern: "Am I duplicating code?"

```python
# Bug #1 Pattern - Copy-paste error
def siguiente_iteracion(self):
    # Lines 109-186: First iteration step
    col_entrante = self._seleccionar_variable_entrante(...)
    fila_saliente, razones = self._seleccionar_variable_saliente(...)
    self._realizar_pivoteo(...)
    # ...
    
    # Lines 188-225: EXACT DUPLICATE!
    # col_entrante = ... (same as line 110)
    # fila_saliente, razones = ... (same as line 134)
    # self._realizar_pivoteo(...) (same as line 154)
```

### Pattern: "Is M-sign correct?"

```python
# Bug #4 Pattern - Unconditional M
fila_z.append(M_PENALIZACION)  # Always +M

# Should be:
# For minimization: penalize by adding -M to objective
# For maximization: penalize by adding +M to objective
# Tableau form standardization means:
# Minimization: fila_z coeff = -M
# Maximization: fila_z coeff = +M
```

### Pattern: "Is index alignment correct?"

```python
# Bug #6 Pattern - Index mismatch
for i in range(num_restricciones):
    a_ij = iteracion.tableau[i][col]  # ← WRONG! Should be i+1
    # tableau[0] is Z-row, tableau[1] is constraint 1, etc.
    # Should be:
    a_ij = iteracion.tableau[i + 1][col]
```

---

## F. Verification Checklist (After Fixes)

### Must Pass All Tests:

**Bug #1 - No Phantom Iterations**
- [ ] Create simple max problem
- [ ] Call `siguiente_iteracion()` once
- [ ] Check: `len(iteraciones) == 2` (not 3)
- [ ] Call again
- [ ] Check: `len(iteraciones) == 3` (not 4 or 5)

**Bug #2 - Immutable History**
- [ ] Create problem and go to iteration 2
- [ ] Save snapshot of `iteraciones[0]`
- [ ] Call `siguiente_iteracion()` again (to iter 3)
- [ ] Check: `iteraciones[0]` unchanged

**Bug #3 - Minimization Works**
- [ ] Create min problem with only <= constraints
- [ ] Solve to completion
- [ ] Check: Correct optimal point found

**Bug #4 - Artificials Eliminated**
- [ ] Create problem with >= or = constraints
- [ ] In Phase 1: artificials in base
- [ ] After Phase 1: no artificials in base
- [ ] Check: `en_fase_1 = False` after few iterations

**Bug #5 - Z-Row Initialized**
- [ ] Create min problem with artificial
- [ ] Check initial Z-row: `tableau[0][-1] < 0` (negative M)
- [ ] Check initial Z-value: `terminos[0] != 0`

**Bug #6 - Index Alignment**
- [ ] Call `_seleccionar_variable_saliente()`
- [ ] Get razones list
- [ ] Check: `len(razones) == num_restricciones`
- [ ] For each i: verify `razones[i]` matches `tableau[i+1]`

---

## G. Files to Edit (Per Bug)

| Bug | File | Action | Approx Lines | Complexity |
|-----|------|--------|--------------|------------|
| #1 | solucionador_simplex.py | DELETE | 188-225 | Trivial (remove code) |
| #2 | solucionador_simplex.py | REFACTOR | 84-170 | Medium (restructure) |
| #3 | solucionador_simplex.py | ADD | ~120 (add param to gran_m.py call) | Easy (pass param) |
| #3b | gran_m.py | ADD | ~1 (receive param in constructor) | Easy (one line) |
| #4 | gran_m.py | MODIFY | 329 | Easy (conditional) |
| #5 | gran_m.py | ADD | ~85 (compute initial Z) | Medium (math) |
| #6 | solucionador_simplex.py | VERIFY | 283-310 | Easy (check indices) |

---

## H. Rollback Points

If you make a mistake, revert to:

**After Bug #1 fix:**
```bash
git checkout HEAD -- solucionador_simplex.py
```

**After Bug #2 fix:**
```bash
git diff HEAD solucionador_simplex.py > bug2.patch
# Review patch
git checkout HEAD -- solucionador_simplex.py  # Revert if needed
```

---

## I. Success Indicators

When Bug #X is fixed, you should see:

| Bug | Success Indicator |
|-----|-------------------|
| #1 | Iteration count increases by 1 per call, not 2 |
| #2 | Previous iterations don't change after new ones created |
| #3 | Minimization problems have different solutions than maximization |
| #4 | Phase 1→2 transition completes instead of hanging |
| #5 | Initial Z-row has non-zero M penalties in it |
| #6 | Minimum ratio highlighting matches printed tableau |

---

## J. Command Snippets

### Find all references to es_minimizacion:
```bash
grep -n "es_minimizacion" core/*.py ui/*.py
```

### Find all mutations of tableau:
```bash
grep -n "tableau\[" core/solucionador_simplex.py | grep "="
```

### Find all _realizar_pivoteo calls:
```bash
grep -n "_realizar_pivoteo" core/solucionador_simplex.py
```

### Check if M is always +M:
```bash
grep -n "M_PENALIZACION" core/gran_m.py
```

### Run simple test:
```bash
python -c "
from core.gran_m import ConstructorPrimerIteracion
from core.solucionador_simplex import SolucionadorSimplex
from core.modelo import Restriccion, TipoRestriccion

constructor = ConstructorPrimerIteracion()
iteracion = constructor.construir_tableau_inicial(
    'x1 + x2',
    'max',
    [Restriccion('x1 + x2', TipoRestriccion.MENOR_IGUAL, '5')]
)
solver = SolucionadorSimplex(iteracion, False)
print(f'Initial iterations: {len(solver.iteraciones)}')
solver.siguiente_iteracion()
print(f'After 1st step: {len(solver.iteraciones)}')
solver.siguiente_iteracion()
print(f'After 2nd step: {len(solver.iteraciones)}')
"
```

---

## K. Documentation by Bug

### Bug #1 (Duplicate Code) - 2 min read
- See: BUG_CASCADE_ANALYSIS.md section B, scenario 1
- Shows: What happens with phantom iterations
- Location: Lines 188-225 are exact copy of 109-186

### Bug #2 (In-place Mutations) - 5 min read
- See: BUG_CASCADE_ANALYSIS.md section E
- Shows: Timeline of mutation and copy
- Location: Line 154 (_realizar_pivoteo) called before line 161 (copy)

### Bug #3 (es_minimizacion ignored) - 3 min read
- See: BUG_CASCADE_ANALYSIS.md section G, paragraph "Mathematical Correctness"
- Shows: Different M-signs for min vs max
- Location: Line 32 stores, nowhere reads

### Bug #4 (Wrong M sign) - 5 min read
- See: BUG_CASCADE_ANALYSIS.md section G
- Shows: Correct fila_z coefficients for min/max
- Location: Line 329 always appends +M

### Bug #5 (Missing Canonicalization) - 7 min read
- See: BUG_CASCADE_ANALYSIS.md section G, paragraph "Initial Z-Row Values"
- Shows: How initial Z should reflect constraint penalties
- Location: Line 85 sets terminos[0] = 0

### Bug #6 (Index Misalignment) - 3 min read
- See: BUG_CASCADE_ANALYSIS.md section F, test case 5
- Shows: Index mapping between reasons and tableau
- Location: Lines 283-310, verify i+1 indexing

