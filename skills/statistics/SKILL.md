---
name: statistics
description: Rigorous statistical inference done correctly — hypothesis tests, confidence intervals, effect sizes, power/sample-size analysis, regression and mixed/GLM models, multiple-comparison correction, bootstrap/resampling, and Bayesian basics. Use when analyzing whether a difference is real, fitting or interpreting a model, checking assumptions, computing power or required n, correcting for many tests, or quantifying uncertainty. Trigger on "is it significant", "t-test", "ANOVA", "regression", "p-value", "confidence interval", "power analysis", "effect size", "mixed model", "correct for multiple comparisons". Uses scipy.stats, statsmodels, pingouin (optional pymc).
---

# Statistics — inference you can defend

Significance is easy to claim and easy to get wrong (assumption violations, p-hacking, ignored
multiplicity, confusing significance with importance). **Run the right test, check its assumptions,
report effect size + uncertainty, and state what the estimate actually covers.**

## Setup
```bash
pip install --break-system-packages scipy statsmodels pingouin numpy pandas
pip install --break-system-packages pymc arviz   # optional, Bayesian
```

## Workflow (every analysis)
1. **Question → estimand.** What population quantity are you estimating (difference in means, odds
   ratio, slope)? Name it before testing.
2. **Pick the method** by data type + design (table below).
3. **Check assumptions** (normality of residuals, equal variance, independence, linearity). If
   violated, switch to a robust/nonparametric/transformed alternative — don't ignore it.
4. **Report:** point estimate, **confidence interval**, **effect size**, test statistic, p-value, n,
   and the assumption checks. The CI and effect size matter more than the p-value.
5. **Correct for multiplicity** when running many tests (Bonferroni / Holm / Benjamini–Hochberg FDR).

## Method picker
| Goal | Default | Robust / alternative |
|---|---|---|
| 2 means, independent | Welch t-test (`scipy.stats.ttest_ind(..., equal_var=False)`) | Mann–Whitney U |
| 2 means, paired | paired t-test | Wilcoxon signed-rank |
| 3+ groups | one-way ANOVA + Tukey HSD | Kruskal–Wallis |
| Proportions | z-test / chi-square / Fisher exact | — |
| Association | Pearson r | Spearman ρ (monotonic) |
| Continuous outcome ~ predictors | OLS (`statsmodels.formula.api.ols`) | robust SE / quantile reg |
| Binary outcome | logistic GLM | — |
| Counts | Poisson / negative-binomial GLM | — |
| Repeated / clustered data | mixed-effects (`statsmodels` MixedLM) | GEE |

## Code patterns
```python
import pingouin as pg, statsmodels.formula.api as smf
pg.ttest(a, b, correction=True)          # t, dof, p, Cohen-d, CI, power — all at once
pg.anova(data=df, dv='y', between='grp', detailed=True); pg.pairwise_tukey(df,'y','grp')
m = smf.ols('y ~ x + C(group)', df).fit(); m.summary()   # check m.resid diagnostics
smf.logit('hit ~ x1 + x2', df).fit().summary()
import statsmodels.stats.multitest as mt
mt.multipletests(pvals, method='fdr_bh')   # multiplicity control
```

**Power / sample size** (do this BEFORE collecting when possible):
```python
from statsmodels.stats.power import TTestIndPower
TTestIndPower().solve_power(effect_size=0.5, alpha=0.05, power=0.8)  # required n per group
```

**Bootstrap** (assumption-light CIs): `scipy.stats.bootstrap`.

**Bayesian (optional)**: small PyMC model → posterior + 94% HDI via ArviZ when you want probability
statements about parameters rather than p-values.

## Guardrails
- Significant ≠ important: always pair p with an effect size and CI.
- Don't interpret a non-significant result as "no effect" — report the CI (it shows what's still plausible).
- Watch for leakage of the hypothesis into the test (pre-register the comparison when you can).
- State assumptions checked and the estimand. Tag claims **Code-verified** (ran the test) vs **Asserted**.
