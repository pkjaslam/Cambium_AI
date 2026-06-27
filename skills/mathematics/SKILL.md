---
name: mathematics
description: Deterministic symbolic and numerical mathematics — compute exact answers instead of estimating. Use whenever a task involves algebra, calculus (derivatives, integrals, limits, series), linear algebra (matrices, determinants, eigenvalues), solving equations or systems, differential equations, simplification/factoring, number theory, units, or any math where correctness matters. Trigger on "solve", "integrate", "differentiate", "simplify", "factor", "expand", "eigenvalues", "solve the ODE", "prove", "evaluate the limit". Uses SymPy (symbolic), NumPy/SciPy (numeric), optional Z3 (logic/constraints) and Pint (units).
---

# Mathematics — exact, verified computation

LLMs estimate arithmetic and routinely make sign, algebra, and bookkeeping errors. **Do not compute
math in your head. Run a deterministic engine and report what it returns.** This skill makes Claude an
exact computational mathematician.

## Setup
```bash
pip install --break-system-packages sympy numpy scipy
# optional power-ups:
pip install --break-system-packages z3-solver pint
```
If a library is missing, install it; never fall back to mental arithmetic for a non-trivial result.

## The rule
1. Translate the problem into SymPy/NumPy.
2. **Run it** (Bash / python).
3. **Verify** the result (substitute back, check identities, sanity-check magnitudes).
4. Report the exact answer, then a decimal if useful, and show the one-line code that produced it.

## Patterns by area (SymPy unless noted)

**Algebra & equations**
```python
import sympy as sp
x, y = sp.symbols('x y', real=True)
sp.solve(sp.Eq(x**2 - 5*x + 6, 0), x)          # [2, 3]
sp.solve([sp.Eq(x+y,3), sp.Eq(x-y,1)], [x,y])  # systems
sp.factor(x**3 - 1); sp.simplify(expr); sp.expand((x+1)**4)
```

**Calculus**
```python
sp.diff(sp.sin(x)*sp.exp(x), x)                 # derivative
sp.integrate(sp.exp(-x**2), (x, -sp.oo, sp.oo)) # sqrt(pi)
sp.limit(sp.sin(x)/x, x, 0)                     # 1
sp.series(sp.cos(x), x, 0, 8)                   # Taylor series
```

**Linear algebra**
```python
M = sp.Matrix([[2,1],[1,3]])
M.det(); M.inv(); M.eigenvals(); M.eigenvects(); M.rref()
```

**Differential equations**
```python
f = sp.Function('f')
sp.dsolve(sp.Eq(f(x).diff(x,2) + f(x), 0), f(x))
```

**Numerics (NumPy/SciPy)** — for large/ill-conditioned or root-finding:
```python
import numpy as np
from scipy import optimize, integrate, linalg
optimize.brentq(lambda t: np.cos(t)-t, 0, 1)    # root
integrate.quad(lambda t: np.exp(-t**2), -np.inf, np.inf)
linalg.eig(A)
```

**Constraints / logic (Z3)** — "is there an integer solution…", SAT/SMT, optimization over constraints.

**Units (Pint)** — carry and convert physical units so dimensional errors are impossible.

## Verification (always)
- Substitute the solution back into the original equation (`expr.subs(x, sol)` → expect 0 / identity).
- Differentiate an integral result to recover the integrand.
- For numerics, check residuals and that the magnitude is plausible.
- Tag the answer: **Proved** (symbolic identity), **Code-verified** (ran + back-substituted), or **Asserted** (couldn't verify — say so).

## Output
Lead with the exact result. Add a decimal approximation when helpful. Show the minimal code. If the
problem is ambiguous (domain, assumptions like real vs complex), state the assumption you used.
