---
name: machine-learning
description: End-to-end predictive modeling done without leakage or self-deception — framing, clean train/validation/test splits, pipelines, cross-validation, hyperparameter tuning, honest evaluation, calibration, and interpretation. Use when building or reviewing a model: classification, regression, feature engineering, model selection, "why is my model overfitting", "which features matter", validation strategy, or putting a model into production. Trigger on "train a model", "predict", "classifier", "regression model", "cross-validation", "feature importance", "overfitting", "XGBoost", "scikit-learn", "PyTorch". Uses scikit-learn, XGBoost, optional PyTorch + SHAP.
---

# Machine learning — models that hold up out of sample

The failure mode isn't bad algorithms — it's **leakage and optimistic evaluation**: fitting on the
test set, tuning on the data you report, or measuring accuracy on imbalanced data. This skill enforces
a disciplined, leak-free workflow.

## Setup
```bash
pip install --break-system-packages scikit-learn xgboost pandas numpy matplotlib
pip install --break-system-packages shap            # interpretation
pip install --break-system-packages torch           # optional, deep learning
```

## The workflow (do not skip steps)
1. **Frame it.** Prediction target, unit of prediction, and the metric that matches the cost of errors
   (not just accuracy — use ROC-AUC / PR-AUC / F1 for imbalance, MAE/RMSE for regression, calibration
   if probabilities are used downstream).
2. **Split FIRST, once.** Hold out a test set before looking at anything. Use **stratified** splits for
   classification and **grouped/time-aware** splits when rows share a subject or have time order — this
   is the #1 leakage guard.
3. **Pipeline everything.** Put imputation, scaling, encoding inside a `Pipeline` so they're fit only on
   training folds — never on the full data.
4. **Cross-validate** on the training set for model selection; tune hyperparameters with nested or
   held-out validation, **never on the test set**.
5. **Evaluate once** on the untouched test set. Report the metric with an uncertainty estimate.
6. **Calibrate & interpret.** Check probability calibration; explain drivers with permutation
   importance or SHAP. Write a short **model card** (data, metric, limits, intended use).

## Reference pattern
```python
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from xgboost import XGBClassifier

X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=.2, stratify=y, random_state=0)
pre = ColumnTransformer([
    ("num", Pipeline([("imp", SimpleImputer()), ("sc", StandardScaler())]), num_cols),
    ("cat", OneHotEncoder(handle_unknown="ignore"), cat_cols),
])
pipe = Pipeline([("pre", pre), ("clf", XGBClassifier(n_estimators=400, max_depth=4,
                 learning_rate=.05, subsample=.8, eval_metric="auc"))])
cv = StratifiedKFold(5, shuffle=True, random_state=0)
print("CV AUC:", cross_val_score(pipe, X_tr, y_tr, cv=cv, scoring="roc_auc").mean())
pipe.fit(X_tr, y_tr)
# evaluate ONCE on the held-out test set:
from sklearn.metrics import roc_auc_score, classification_report
print("TEST AUC:", roc_auc_score(y_te, pipe.predict_proba(X_te)[:,1]))
```

## Leakage checklist (run mentally every time)
- Was any scaler/encoder/imputer/feature-selection fit on data that includes the test rows? → leak.
- Do features include information unavailable at prediction time (future data, target-derived)? → leak.
- Rows sharing a subject/group split across train and test? → use `GroupKFold`.
- Time series split randomly instead of by time? → use `TimeSeriesSplit`.
- Tuned on the test set / reported the best of many runs? → optimistic; use nested CV.

## Guardrails
- Always compare against a **baseline** (majority class / simple linear model) — a fancy model that
  barely beats the baseline isn't worth it.
- Report the metric that matches the decision, with a CI or CV spread, not a single lucky number.
- Tag results **Code-verified** (real held-out evaluation) vs **Asserted**. State the model's limits.
