---
name: optimization
description: Formulate and solve optimization problems correctly — linear, mixed-integer, convex, nonlinear, and constraint problems. Use when minimizing/maximizing an objective subject to constraints, scheduling/allocation/assignment, portfolio or resource optimization, curve fitting, or "find the best X subject to Y". Trigger on "minimize", "maximize", "subject to", "optimal allocation", "linear program", "integer program", "least squares", "constraint solver". Uses scipy.optimize, cvxpy (convex), PuLP / OR-Tools (LP/MILP), and reports whether the solution is a verified global optimum or only local.
---

# Optimization — formulate, solve, and prove optimality status

The danger is a confident-looking number that is actually infeasible, a local minimum, or the answer to
the wrong formulation. **Write the model explicitly (variables · objective · constraints), pick the
solver that matches its structure, and report the optimality status the solver returns.**

## Setup
```bash
pip install --break-system-packages scipy numpy
pip install --break-system-packages cvxpy pulp ortools   # as needed
```

## Choose the solver by structure
| Problem | Use | Guarantee |
|---|---|---|
| Linear obj + linear constraints (continuous) | `scipy.optimize.linprog` / PuLP | global |
| Integer / binary decisions (MILP) | PuLP or OR-Tools | global (proven) |
| Convex (LS, QP, SOCP, many ML losses) | **cvxpy** | global |
| Smooth nonlinear + constraints | `scipy.optimize.minimize` (SLSQP/trust-constr) | **local only** |
| Curve / least-squares fit | `scipy.optimize.curve_fit` / `least_squares` | local |
| Combinatorial (routing, scheduling) | OR-Tools | depends |

## Patterns
**Linear program**
```python
from scipy.optimize import linprog
# minimize c·x  s.t.  A_ub x <= b_ub,  bounds
res = linprog(c, A_ub=A, b_ub=b, bounds=bnds, method="highs")
print(res.status, res.message, res.fun, res.x)   # status 0 = optimal
```

**Mixed-integer (PuLP)**
```python
import pulp
m = pulp.LpProblem("alloc", pulp.LpMaximize)
x = pulp.LpVariable.dicts("x", items, lowBound=0, cat="Integer")
m += pulp.lpSum(value[i]*x[i] for i in items)            # objective
m += pulp.lpSum(weight[i]*x[i] for i in items) <= cap     # constraint
m.solve(); print(pulp.LpStatus[m.status])                 # "Optimal"
```

**Convex (cvxpy)** — preferred when the problem is convex; gives a global optimum + dual values:
```python
import cvxpy as cp
x = cp.Variable(n, nonneg=True)
prob = cp.Problem(cp.Minimize(cp.sum_squares(A@x - b)), [cp.sum(x) == 1])
prob.solve(); print(prob.status, prob.value)
```

## Discipline
1. **State the model** in words and math before coding: decision variables, objective (min/max), every
   constraint, variable domains (continuous/integer/binary).
2. **Check feasibility first** — an infeasible/unbounded status means the model is wrong, not "no answer."
3. **Report the status** the solver returns (optimal / infeasible / unbounded / local). For nonlinear
   solvers, say explicitly it's a **local** optimum and try multiple starts.
4. **Verify** the returned point satisfies every constraint (substitute back) and recompute the objective.
5. Tag the result **Code-verified** (solver returned optimal + constraints checked) vs **Asserted**.

## Guardrails
- Never claim "optimal" for a local nonlinear result — say "best found from N starts."
- Watch units/scaling — badly scaled constraints cause solver failures; normalize.
- Prefer a convex formulation when possible; it turns "a local guess" into "the global answer."
