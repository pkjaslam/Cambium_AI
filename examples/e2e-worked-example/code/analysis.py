#!/usr/bin/env python3
"""Reproducible headline computation for the Cambium e2e worked example.
Deterministic (fixed data, no RNG) -> bit-for-bit reproducible -> a stable output hash."""
import statistics, math
# fictional agricultural field trial: treatment-minus-control yield gain (bu/acre), 12 plots
GAINS = [3.1, 2.4, 3.8, 2.9, 3.3, 2.7, 3.5, 3.0, 2.6, 3.2, 2.8, 3.4]
n = len(GAINS); mean = statistics.mean(GAINS); sd = statistics.stdev(GAINS)
se = sd / math.sqrt(n); t = mean / se; ci = 1.96 * se
print(f"n={n} mean_gain={mean:.3f} sd={sd:.3f} t={t:.2f} ci95=[{mean-ci:.3f},{mean+ci:.3f}]")
print(f"HEADLINE: treatment increased yield by {mean:.2f} bu/acre "
      f"(95% CI {mean-ci:.2f}-{mean+ci:.2f}, t={t:.1f}, n={n})")
