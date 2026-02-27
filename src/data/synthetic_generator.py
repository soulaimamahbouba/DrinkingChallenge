"""
Synthetic time-series generator for AquaGuard demo.

Takes the static Kaggle CSV and produces realistic 5-minute sensor streams
for multiple monitoring sites, including injected degradation events.
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from config import (
    DATA_RAW, DATA_SYNTH, SENSOR_MAP, SENSOR_COLS, TARGET_COL,
    SITES, SAMPLE_INTERVAL_MIN, STREAM_DAYS, THRESHOLDS, CAUSE_CLASSES,
)

np.random.seed(42)


def load_base_stats(csv_path=None):
    """Compute per-sensor mean/std from the Kaggle CSV."""
    if csv_path is None:
        csv_path = DATA_RAW / "water_potability.csv"
    df = pd.read_csv(csv_path)
    df = df.rename(columns=SENSOR_MAP)
    stats = {}
    for col in SENSOR_COLS:
        if col in df.columns:
            stats[col] = {"mean": df[col].mean(), "std": df[col].std()}
    return stats


def _diurnal(t: pd.Timestamp) -> float:
    """Diurnal multiplier: peaks at 7am and 7pm (demand hours)."""
    hour = t.hour + t.minute / 60
    return 1 + 0.08 * np.sin(2 * np.pi * (hour - 7) / 24) + \
           0.04 * np.sin(4 * np.pi * (hour - 7) / 24)


def _add_noise(series: pd.Series, noise_pct=0.02):
    """Add Gaussian noise proportional to mean."""
    return series + np.random.normal(0, abs(series.mean()) * noise_pct, len(series))


def generate_baseline_stream(stats: dict, n_points: int, start: datetime) -> pd.DataFrame:
    """Generate a smooth, realistic baseline sensor stream."""
    timestamps = pd.date_range(start, periods=n_points, freq=f"{SAMPLE_INTERVAL_MIN}min")
    df = pd.DataFrame({"timestamp": timestamps})

    for col in SENSOR_COLS:
        s = stats.get(col, {"mean": 10, "std": 2})
        mean, std = s["mean"], s["std"]

        # AR(1) correlated process (realistic sensor drift)
        ar_coef = 0.98
        vals = np.zeros(n_points)
        vals[0] = mean
        for i in range(1, n_points):
            vals[i] = ar_coef * vals[i - 1] + (1 - ar_coef) * mean + np.random.normal(0, std * 0.03)

        # Apply diurnal pattern to flow-sensitive sensors
        if col in ["chloramine", "turbidity", "conductivity", "ph"]:
            diurnal = np.array([_diurnal(t) for t in timestamps])
            vals = vals * diurnal

        # Clip to physically realistic ranges
        if col in THRESHOLDS:
            lo = THRESHOLDS[col]["low"] * 0.5  # allow slight sub-threshold
            hi = THRESHOLDS[col]["high"] * 1.5
            vals = np.clip(vals, lo, hi)

        df[col] = _add_noise(pd.Series(vals))

    df[TARGET_COL] = 1  # baseline is potable
    df["event_type"] = "normal"
    return df


# ── Event injection ─────────────────────────────────────
def inject_disinfectant_decay(df: pd.DataFrame, start_idx: int, duration: int = 60):
    """Chloramine drops, THM rises — disinfection failure."""
    end = min(start_idx + duration, len(df))
    ramp = np.linspace(0, 1, end - start_idx)
    df.loc[start_idx:end - 1, "chloramine"] *= (1 - 0.7 * ramp)  # drop to 30%
    df.loc[start_idx:end - 1, "thm"] *= (1 + 0.8 * ramp)
    df.loc[start_idx:end - 1, "event_type"] = "disinfectant_decay"
    df.loc[start_idx:end - 1, TARGET_COL] = 0
    return df


def inject_contamination(df: pd.DataFrame, start_idx: int, duration: int = 40):
    """Sudden turbidity spike + conductivity jump — pipe intrusion."""
    end = min(start_idx + duration, len(df))
    ramp = np.concatenate([np.linspace(0, 1, (end - start_idx) // 2),
                           np.linspace(1, 0.6, (end - start_idx) - (end - start_idx) // 2)])
    df.loc[start_idx:end - 1, "turbidity"] += 3.0 * ramp
    df.loc[start_idx:end - 1, "conductivity"] += 200 * ramp
    df.loc[start_idx:end - 1, "organic_carbon"] += 5 * ramp
    df.loc[start_idx:end - 1, "event_type"] = "contamination_intrusion"
    df.loc[start_idx:end - 1, TARGET_COL] = 0
    return df


def inject_corrosion(df: pd.DataFrame, start_idx: int, duration: int = 80):
    """Slow pH drop + conductivity rise — pipe corrosion / leaching."""
    end = min(start_idx + duration, len(df))
    ramp = np.linspace(0, 1, end - start_idx)
    df.loc[start_idx:end - 1, "ph"] -= 1.5 * ramp
    df.loc[start_idx:end - 1, "conductivity"] += 100 * ramp
    df.loc[start_idx:end - 1, "hardness"] += 40 * ramp
    df.loc[start_idx:end - 1, "event_type"] = "pipe_corrosion"
    df.loc[start_idx:end - 1, TARGET_COL] = 0
    return df


def inject_stagnation(df: pd.DataFrame, start_idx: int, duration: int = 100):
    """Chloramine slowly drops, turbidity slightly rises — dead-end pipe."""
    end = min(start_idx + duration, len(df))
    ramp = np.linspace(0, 1, end - start_idx)
    df.loc[start_idx:end - 1, "chloramine"] *= (1 - 0.5 * ramp)
    df.loc[start_idx:end - 1, "turbidity"] += 0.8 * ramp
    df.loc[start_idx:end - 1, "event_type"] = "stagnation"
    df.loc[start_idx:end - 1, TARGET_COL] = 0
    return df


def inject_sensor_fault(df: pd.DataFrame, start_idx: int, duration: int = 50):
    """Stuck sensor value — pH flatlines."""
    end = min(start_idx + duration, len(df))
    stuck_val = df.loc[start_idx, "ph"]
    df.loc[start_idx:end - 1, "ph"] = stuck_val  # zero variance
    df.loc[start_idx:end - 1, "event_type"] = "sensor_fault"
    # Potability unknown but system should flag
    return df


EVENT_INJECTORS = {
    "disinfectant_decay": inject_disinfectant_decay,
    "contamination_intrusion": inject_contamination,
    "pipe_corrosion": inject_corrosion,
    "stagnation": inject_stagnation,
    "sensor_fault": inject_sensor_fault,
}


def generate_site_data(site_name: str, stats: dict, days: int = STREAM_DAYS) -> pd.DataFrame:
    """Generate full synthetic stream for one site with injected events."""
    n_points = days * 24 * 60 // SAMPLE_INTERVAL_MIN  # 5-min intervals
    start = datetime(2026, 1, 1)
    df = generate_baseline_stream(stats, n_points, start)
    df["site"] = site_name

    # Inject 2-4 events per site at random non-overlapping positions
    n_events = np.random.randint(3, 6)
    event_types = list(EVENT_INJECTORS.keys())
    positions = sorted(np.random.choice(range(500, n_points - 200), n_events, replace=False))

    for i, pos in enumerate(positions):
        etype = event_types[i % len(event_types)]
        df = EVENT_INJECTORS[etype](df, pos)

    return df


def generate_all_sites():
    """Generate and save synthetic data for all monitoring sites."""
    stats = load_base_stats()
    DATA_SYNTH.mkdir(parents=True, exist_ok=True)
    all_dfs = []

    for site in SITES:
        print(f"  Generating stream for {site}...")
        df = generate_site_data(site, stats)
        df.to_parquet(DATA_SYNTH / f"{site}.parquet", index=False)
        all_dfs.append(df)

    combined = pd.concat(all_dfs, ignore_index=True)
    combined.to_parquet(DATA_SYNTH / "all_sites.parquet", index=False)
    print(f"  ✓ Generated {len(combined):,} rows for {len(SITES)} sites")
    print(f"  Event distribution:\n{combined['event_type'].value_counts().to_string()}")
    return combined


if __name__ == "__main__":
    generate_all_sites()
