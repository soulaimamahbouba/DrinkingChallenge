"""
Model training pipeline for AquaGuard.

1) Binary potability classifier (LightGBM) — "will water be non-potable?"
2) Multi-class cause classifier — "what is the probable cause?"
3) Anomaly scorer — residual-based risk amplifier

Uses blocked time-series cross-validation.
"""
import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import (
    roc_auc_score, classification_report, f1_score,
    mean_absolute_error, confusion_matrix,
)
import joblib
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from config import (
    DATA_SYNTH, MODEL_DIR, LGBM_PARAMS, TARGET_COL,
    CAUSE_CLASSES, SENSOR_COLS,
)
from src.features.engineering import build_features


def load_training_data():
    """Load synthetic data and build features per site."""
    df = pd.read_parquet(DATA_SYNTH / "all_sites.parquet")
    # Sort by site then timestamp for proper time-series ordering
    df = df.sort_values(["site", "timestamp"]).reset_index(drop=True)
    featured, feature_cols = build_features(df, include_target=True)
    return featured, feature_cols


def blocked_time_series_split(df, n_splits=4):
    """
    Blocked time-series CV: split data into n_splits blocks,
    train on first k blocks, validate on block k+1.
    """
    sites = df["site"].unique()
    for fold in range(1, n_splits):
        train_indices, val_indices = [], []
        for site in sites:
            site_df = df[df["site"] == site]
            n = len(site_df)
            block_size = n // n_splits
            train_end = block_size * fold
            val_end = block_size * (fold + 1)
            train_indices.extend(site_df.index[:train_end].tolist())
            val_indices.extend(site_df.index[train_end:val_end].tolist())
        yield train_indices, val_indices


# ── 1. Potability classifier ───────────────────────────
def train_potability_model(df, feature_cols):
    """Train LightGBM binary classifier for potability prediction."""
    print("\n=== Training Potability Classifier ===")
    X = df[feature_cols].values
    y = df[TARGET_COL].values

    # Single train/val split (last 25% as validation)
    split_idx = int(len(df) * 0.75)
    X_train, X_val = X[:split_idx], X[split_idx:]
    y_train, y_val = y[:split_idx], y[split_idx:]

    params = LGBM_PARAMS.copy()
    model = lgb.LGBMClassifier(**params)
    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
    )

    # Evaluate
    y_pred_proba = model.predict_proba(X_val)[:, 1]
    y_pred = model.predict(X_val)
    auc = roc_auc_score(y_val, y_pred_proba)
    print(f"  Validation AUC: {auc:.4f}")
    print(classification_report(y_val, y_pred, target_names=["Non-Potable", "Potable"]))

    # Feature importance
    importance = pd.DataFrame({
        "feature": feature_cols,
        "importance": model.feature_importances_
    }).sort_values("importance", ascending=False)
    print("  Top 15 features:")
    print(importance.head(15).to_string(index=False))

    return model, importance


# ── 2. Cause classifier ────────────────────────────────
def train_cause_model(df, feature_cols):
    """Train multi-class LightGBM for probable cause identification."""
    print("\n=== Training Cause Classifier ===")

    # Encode cause labels
    cause_map = {c: i for i, c in enumerate(CAUSE_CLASSES)}
    df = df.copy()
    df["cause_label"] = df["event_type"].map(cause_map).fillna(0).astype(int)

    X = df[feature_cols].values
    y = df["cause_label"].values

    split_idx = int(len(df) * 0.75)
    X_train, X_val = X[:split_idx], X[split_idx:]
    y_train, y_val = y[:split_idx], y[split_idx:]

    params = LGBM_PARAMS.copy()
    params["objective"] = "multiclass"
    params["metric"] = "multi_logloss"
    params["num_class"] = len(CAUSE_CLASSES)

    model = lgb.LGBMClassifier(**params)
    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
    )

    y_pred = model.predict(X_val)
    present_labels = sorted(set(y_val) | set(y_pred))
    present_names = [CAUSE_CLASSES[i] for i in present_labels]
    macro_f1 = f1_score(y_val, y_pred, average="macro")
    print(f"  Macro-F1: {macro_f1:.4f}")
    print(classification_report(y_val, y_pred, labels=present_labels, target_names=present_names))

    return model


# ── 3. Forecasting model (per-sensor) ──────────────────
def train_forecast_models(df, feature_cols, horizon=12):
    """
    Train a regression model per sensor to predict value at t+horizon.
    Used for anomaly scoring: actual vs predicted residual.
    """
    print("\n=== Training Forecast Models ===")
    models = {}
    for col in SENSOR_COLS:
        if col not in df.columns:
            continue

        # Create target: future value
        target = df[col].shift(-horizon)
        mask = target.notna()
        X = df.loc[mask, feature_cols].values
        y = target[mask].values

        split_idx = int(len(X) * 0.75)
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]

        params = LGBM_PARAMS.copy()
        params["objective"] = "regression"
        params["metric"] = "mae"
        del params["early_stopping_rounds"]  # handle via callback

        model = lgb.LGBMRegressor(**params)
        model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
        )

        y_pred = model.predict(X_val)
        mae = mean_absolute_error(y_val, y_pred)
        print(f"  {col}: MAE={mae:.4f}")
        models[col] = model

    return models


# ── Main training pipeline ──────────────────────────────
def train_all():
    """Train all models and save to disk."""
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    df, feature_cols = load_training_data()
    print(f"Training data: {len(df):,} rows, {len(feature_cols)} features")

    # Save feature column list
    joblib.dump(feature_cols, MODEL_DIR / "feature_cols.pkl")

    # 1. Potability model
    pot_model, importance = train_potability_model(df, feature_cols)
    joblib.dump(pot_model, MODEL_DIR / "potability_lgbm.pkl")
    importance.to_csv(MODEL_DIR / "feature_importance.csv", index=False)

    # 2. Cause model
    cause_model = train_cause_model(df, feature_cols)
    joblib.dump(cause_model, MODEL_DIR / "cause_lgbm.pkl")

    # 3. Forecast models
    forecast_models = train_forecast_models(df, feature_cols)
    joblib.dump(forecast_models, MODEL_DIR / "forecast_models.pkl")

    print("\nAll models saved to", MODEL_DIR)
    return pot_model, cause_model, forecast_models


if __name__ == "__main__":
    train_all()
