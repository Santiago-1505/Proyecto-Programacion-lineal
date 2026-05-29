# BUG CASCADE ANALYSIS - EXECUTIVE SUMMARY

## Quick Reference

### DEPENDENCY CHAIN
```
Fix #1 (duplicate code)
    ↓
Fix #2 (in-place mutations)
    ↓
Fix #3 (use es_minimizacion)
    ↓
Fix #4 (M sign for min/max)
    ↓
Fix #5 (Z-row canonicalization)
    ↓
Fix #6 (index alignment)
```

**Cannot skip any step.** Each fix depends on previous ones being correct.

---

## THE 6 BUGS IN ONE TABLE

| # | Bug | Location | Impact | Fix Order | Skip=Risk |
|---|-----|----------|--------|-----------|-----------|
| 1 | **Duplicate code** | `siguiente_iteracion()` lines 188-225 | Phantom iterations in history | **1st MUST** | History corrupted forever |
| 2 | **In-place mutations** | `_realizar_pivoteo()` + `_crear_siguiente_iteracion()` | Previous iterations change after new ones | **2nd MUST** | Phase transitions fail; all history wrong |
| 3 | **es_minimizacion ignored** | Not stored in `__init__`; not used | Minimization problems treated as max | **3rd** | Minimization broken |
| 4 | **Wrong M sign** | Always `+M` in line 329 | Artificials never penalized correctly | **4th** | Phase 1 never eliminates artificials |
| 5 | **Missing canonicalization** | Initial Z-row not adjusted | Z-value wrong; suboptimal pivots | **5th** | Numerical instability; wrong solution |
| 6 | **Index misalignment** | Reasons list vs. tableau rows | UI highlights wrong cells | **6th** | Poor visualization only |

---

## CRITICAL SCENARIOS

### Scenario A: Just Remove Duplicate Code (Bug #1 only)
**Result:** WORSE
- Iterations no longer double
- BUT previous iterations still get mutated
- UI thinks it solved in 2 iterations, but each is wrong
- "Solution" values garbage

### Scenario B: Fix Bugs #1 + #2
**Result:** Good for maximization with <=
- History immutable and correct
- Simple max problems work
- BUT: Minimization fails, artificials aren't eliminated, unbounded detection fails

### Scenario C: Fix Bugs #1 + #2 + #3
**Result:** Minimization still fails
- Code now READS es_minimizacion
- BUT: Still uses +M for all artificials (Bug #4)
- Minimization tries to minimize artificials by adding them (wrong sign)
- Phase 1 never terminates

### Scenario D: Fix ALL 6
**Result:** CORRECT
- History immutable
- Min/Max both work
- Artificials eliminated in Phase 1
- Phase 2 optimal solutions correct
- UI visualization precise

---

## MATHEMATICAL FOUNDATION

### What SHOULD happen in Gran M

For **MINIMIZATION** with artificial:
```
Objective: min(c1*x1 + c2*x2 + M*A1 + M*A2)
Tableau: Z - c1*x1 - c2*x2 - M*A1 - M*A2 = 0
fila_z:  [-c1, -c2, 0, 0, ..., -M, -M, ...]
                                  ↑
                         NEGATIVE M (penalizes artificials)
```

For **MAXIMIZATION** with artificial:
```
Objective: max(c1*x1 + c2*x2 - M*A1 - M*A2)
Tableau: Z - c1*x1 - c2*x2 + M*A1 + M*A2 = 0
fila_z:  [-c1, -c2, 0, 0, ..., +M, +M, ...]
                                  ↑
                         POSITIVE M (penalizes artificials)
```

### Current Code (BROKEN)
```python
fila_z.append(M_PENALIZACION)  # Always +M, never -M
# Should be:
# fila_z.append(-M_PENALIZACION if es_minimizacion else M_PENALIZACION)
```

---

## THE MUTATION BUG IN PICTURES

**Expected (with fix):**
```
Iteration 0:  [[1, 2], [3, 4]]
                  ↓ (copy, pivot on copy, create iter 1)
Iteration 1:  [[1, 0.5], [0, 1]]
Iteration 0:  [[1, 2], [3, 4]]  ← UNCHANGED
                  ↓ (copy, pivot on copy, create iter 2)
Iteration 2:  [[X, Y], [Z, W]]
Iteration 0:  [[1, 2], [3, 4]]  ← STILL UNCHANGED
```

**Actual (with Bug #2):**
```
Iteration 0:  [[1, 2], [3, 4]]
                  ↓ (pivot IN PLACE, then copy)
Iteration 0:  [[1, 0.5], [0, 1]]  ← MUTATED!
Iteration 1:  [[1, 0.5], [0, 1]]
                  ↓ (pivot IN PLACE, then copy)
Iteration 0:  [[A, B], [C, D]]  ← MUTATED AGAIN!
Iteration 1:  [[A, B], [C, D]]  ← ALSO CHANGED!
Iteration 2:  [[A, B], [C, D]]
```

---

## CONCRETE TEST CASES

### Test 1: Bug #1 Fixed
```python
# Simple max problem: should have 2 iterations total
solver = SolucionadorSimplex(iter_inicial, False)
solver.siguiente_iteracion()
assert len(solver.iteraciones) == 2  # NOT 3
```

### Test 2: Bug #2 Fixed
```python
# After creating iter1, iter0 should be unchanged
tableau0_before = solver.iteraciones[0].tableau
solver.siguiente_iteracion()
assert solver.iteraciones[0].tableau == tableau0_before
```

### Test 3: Bug #3+#4 Fixed
```python
# Minimization with >= constraint
solver = SolucionadorSimplex(iter_inicial, es_minimizacion=True)
solver.siguiente_iteracion()
# Artificial should START being eliminated (not added to Z)
```

### Test 4: Bug #5 Fixed
```python
# Initial Z-row should include M penalties from constraints
# NOT just zeros
artificial_coeff = iteracion.tableau[0][-1]
assert artificial_coeff < 0  # For minimization, should be -M
```

### Test 5: Bug #6 Fixed
```python
# Reasons list should align with constraints
num_reasons = len(razones)
num_constraints = iteracion.obtener_num_restricciones()
assert num_reasons == num_constraints
```

---

## TIMELINE: What to Fix First

```
PHASE 1 (CRITICAL - Do These First):
  ✓ Remove lines 188-225 (duplicate code)
  ✓ Implement copy-before-pivot

PHASE 2 (CORE LOGIC):
  ✓ Store tipo_optimizacion in SolucionadorSimplex
  ✓ Use it to set M-sign correctly
  ✓ Compute initial Z-row with constraint penalties

PHASE 3 (POLISH):
  ✓ Align index mapping for visualization
  ✓ Run regression tests
```

---

## WHICH FILES TOUCH WHAT

| File | Bug #1 | Bug #2 | Bug #3 | Bug #4 | Bug #5 | Bug #6 |
|------|--------|--------|--------|--------|--------|--------|
| `solucionador_simplex.py` | ✓ | ✓ | ✓ | - | - | ✓ |
| `gran_m.py` | - | - | - | ✓ | ✓ | - |
| `modelo.py` | - | - | - | - | - | - |
| UI files | ✓ affected | ✓ affected | - | - | - | ✓ affected |

---

## RISK: WHAT BREAKS IF WE DON'T FIX

### Risk Level: CRITICAL
- **Bug #1:** History is garbage. Cannot be worked around.
- **Bug #2:** Previous iterations mutate. Cannot see history correctly.

### Risk Level: HIGH
- **Bug #3:** Minimization doesn't work. All min problems wrong.
- **Bug #4:** Artificials aren't eliminated. Phase 1 fails.

### Risk Level: MEDIUM
- **Bug #5:** Numerical instability. Suboptimal path chosen.

### Risk Level: LOW
- **Bug #6:** Visualization confusing. Math correct but UI wrong.

---

## PROOF CHECKLIST

After fixing, verify:

- [ ] Each call to `siguiente_iteracion()` adds exactly 1 iteration
- [ ] Previous iterations never change after new ones created
- [ ] Minimization problems converge to correct solution
- [ ] Maximization problems converge to correct solution
- [ ] Phase 1 (artificial elimination) works correctly
- [ ] Phase 2 (optimization) works correctly
- [ ] Unbounded problems detected correctly
- [ ] Infeasible problems detected correctly
- [ ] UI shows correct iteration numbers and counts
- [ ] Minimum ratio highlighting points to correct rows

---

## FILE LOCATION

Full analysis: `BUG_CASCADE_ANALYSIS.md`
This summary: `BUG_EXECUTIVE_SUMMARY.md`

