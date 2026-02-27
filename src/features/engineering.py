"""
Feature engineering for AquaGuard.

Produces time-window features from raw sensor streams:
- Rolling statistics (mean, std, min, max, range)
- Exponentially weighted moving average (EWMA)
- Rate of change (first derivative)
- Lag features
- Hour-of-day / day-of-week cyclical encodings
- Cross-sensor ratios (domain-specific)
"""
import numpy as np
import pandas as pd
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from config import SENSOR_COLS, WINDOW_SIZES


def add_temporal_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add cyclical time encodings."""
    df = df.copy()
    ts = pd.to_datetime(df["timestamp"])
    hour = ts.dt.hour + ts.dt.minute / 60
    df["hour_sin"] = np.sin(2 * np.pi * hour / 24)
    df["hour_cos"] = np.cos(2 * np.pi * hour / 24)
    df["dow_sin"] = np.sin(2 * np.pi * ts.dt.dayofweek / 7)
    df["dow_cos"] = np.cos(2 * np.pi * ts.dt.dayofweek / 7)
    df["is_night"] = ((ts.dt.hour >= 22) | (ts.dt.hour < 6)).astype(int)
    return df


def add_rolling_features(df: pd.DataFrame, sensors=None, windows=None) -> pd.DataFrame:
    """Rolling statistics for each sensor."""
    df = df.copy()
    sensors = sensors or SENSOR_COLS
    windows = windows or WINDOW_SIZES

    for col in sensors:
        if col not in df.columns:
            continue
        s = df[col]
        for w in windows:
            prefix = f"{col}_w{w}"
            df[f"{prefix}_mean"] = s.rolling(w, min_periods=1).mean()
            df[f"{prefix}_std"] = s.rolling(w, min_periods=1).std().fillna(0)
            df[f"{prefix}_min"] = s.rolling(w, min_periods=1).min()
            df[f"{prefix}_max"] = s.rolling(w, min_periods=1).max()
            df[f"{prefix}_range"] = df[f"{prefix}_max"] - df[f"{prefix}_min"]
    return df


def add_ewma_features(df: pd.DataFrame, sensors=None, spans=(6, 24)) -> pd.DataFrame:
    """Exponentially weighted moving average."""
    df = df.copy()
    sensors = sensors or SENSOR_COLS
    for col in sensors:
        if col not in df.columns:
            continue
        for span in spans:
            df[f"{col}_ewma_{span}"] = df[col].ewm(span=span, min_periods=1).mean()
    return df


def add_derivative_features(df: pd.DataFrame, sensors=None) -> pd.DataFrame:
    """Rate of change (first derivative via diff)."""
    df = df.copy()
    sensors = sensors or SENSOR_COLS
    for col in sensors:
        if col not in df.columns:
            continue
        df[f"{col}_diff1"] = df[col].diff().fillna(0)
        df[f"{col}_diff3"] = df[col].diff(3).fillna(0)
    return df


def add_lag_features(df: pd.DataFrame, sensors=None, lags=(1, 3, 6, 12)) -> pd.DataFrame:
    """Lag features for autoregressive signal."""
    df = df.copy()
    sensors = sensors or SENSOR_COLS
    for col in sensors:
        if col not in df.columns:
            continue
        for lag in lags:
            df[f"{col}_lag{lag}"] = df[col].shift(lag).bfill()
    return df


def add_cross_sensor_ratios(df: pd.DataFrame) -> pd.DataFrame:
    """Domain-specific cross-sensor features."""
    df = df.copy()
    if "chloramine" in df.columns and "turbidity" in df.columns:
        df["chlor_turb_ratio"] = df["chloramine"] / (df["turbidity"] + 0.01)
    if "conductivity" in df.columns and "tds" in df.columns:
        df["cond_tds_ratio"] = df["conductivity"] / (df["tds"] + 1)
    if "ph" in df.columns and "hardness" in df.columns:
        df["ph_hardness_ratio"] = df["ph"] / (df["hardness"] + 1)
    if "organic_carbon" in df.columns and "thm" in df.columns:
        df["oc_thm_ratio"] = df["organic_carbon"] / (df["thm"] + 0.01)
    return df


def add_stuck_sensor_flags(df: pd.DataFrame, sensors=None, window=12) -> pd.DataFrame:
    """Flag sensors with zero variance over a window (stuck sensor detection)."""
    df = df.copy()
    sensors = sensors or SENSOR_COLS
    for col in sensors:
        if col not in df.columns:
            continue
        rolling_std = df[col].rolling(window, min_periods=1).std().fillna(0)
        df[f"{col}_stuck"] = (rolling_std < 1e-6).astype(int)
    return df


def build_features(df: pd.DataFrame, include_target=True) -> pd.DataFrame:
    """Full feature engineering pipeline."""
    df = add_temporal_features(df)
    df = add_rolling_features(df)
    df = add_ewma_features(df)
    df = add_derivative_features(df)
    df = add_lag_features(df)
    df = add_cross_sensor_ratios(df)
    df = add_stuck_sensor_flags(df)

    # Drop rows with NaN from rolling (first few rows)
    df = df.dropna(subset=[c for c in df.columns if c not in ["timestamp", "site", "event_type"]])

    # Feature columns = everything except meta
    meta_cols = {"timestamp", "site", "event_type", "potability"} if include_target else {"timestamp", "site", "event_type"}
    feature_cols = sorted([c for c in df.columns if c not in meta_cols])

    return df, feature_cols


if __name__ == "__main__":
    # Quick test
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
    from config import DATA_SYNTH
    df = pd.read_parquet(DATA_SYNTH / "all_sites.parquet")
    site_df = df[df["site"] == "WTP_Outlet"].head(2000).copy()
    featured, cols = build_features(site_df)
    print(f"Features: {len(cols)} columns, {len(featured)} rows")
    print("Sample columns:", cols[:20])
