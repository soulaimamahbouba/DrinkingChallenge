"""
Water Quality Risk Index (WQRI) — 0-100 composite score.

Design:
  - Each sensor gets a "deviation score" (0–100) based on distance from safe range
  - Weighted aggregation using domain-driven weights
  - EWMA smoothing to reduce flicker / false alarms
  - Hysteresis for alert state transitions

Score interpretation:
  0-30: Excellent — all parameters within safe ranges
  30-50: Normal — minor deviations, monitoring
  50-65: Caution — approaching regulatory limits
  65-80: Warning — likely non-compliant, investigate
  80-100: Critical — immediate action required
"""
import numpy as np
import pandas as pd
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from config import THRESHOLDS, RISK_WEIGHTS, SENSOR_COLS


def sensor_deviation_score(value: float, sensor: str) -> float:
    """
    Map a sensor value to 0-100 deviation score.
    0 = perfectly within safe range
    100 = extreme violation
    """
    if sensor not in THRESHOLDS or pd.isna(value):
        return 0.0

    th = THRESHOLDS[sensor]
    lo, hi = th["low"], th["high"]
    mid = (lo + hi) / 2
    safe_range = (hi - lo) / 2

    if safe_range == 0:
        safe_range = 1.0

    if lo <= value <= hi:
        # Within range: score 0-30 based on distance from center
        dist = abs(value - mid) / safe_range
        return min(30.0 * dist, 30.0)
    else:
        # Outside range: score 30-100 based on overshoot
        if value < lo:
            overshoot = (lo - value) / safe_range
        else:
            overshoot = (value - hi) / safe_range
        return min(30.0 + 70.0 * overshoot, 100.0)


def compute_risk_index(row: pd.Series) -> float:
    """
    Compute weighted risk index for a single reading.
    Returns: float 0-100
    """
    total_weight = 0
    weighted_score = 0

    for sensor, weight in RISK_WEIGHTS.items():
        if sensor in row.index and not pd.isna(row[sensor]):
            score = sensor_deviation_score(row[sensor], sensor)
            weighted_score += weight * score
            total_weight += weight

    if total_weight == 0:
        return 0.0
    return weighted_score / total_weight


def compute_risk_series(df: pd.DataFrame, ewma_span: int = 6) -> pd.Series:
    """
    Compute smoothed risk index for entire DataFrame.
    EWMA smoothing reduces noise and flicker.
    """
    raw_risk = df.apply(compute_risk_index, axis=1)
    smoothed = raw_risk.ewm(span=ewma_span, min_periods=1).mean()
    return smoothed.clip(0, 100)


def apply_alert_logic(risk_series: pd.Series,
                      warn_threshold: float = 65,
                      crit_threshold: float = 80,
                      persistence: int = 3,
                      hysteresis: float = 5) -> pd.DataFrame:
    """
    Stateful alerting with persistence and hysteresis.

    Returns DataFrame with columns: risk, alert_level, alert_changed
    alert_level: 'normal', 'warning', 'critical'
    """
    alerts = pd.DataFrame({
        "risk": risk_series.values,
        "alert_level": "normal",
        "alert_changed": False,
    }, index=risk_series.index)

    current_state = "normal"
    consecutive_above_warn = 0
    consecutive_above_crit = 0

    for i in range(len(risk_series)):
        risk = risk_series.iloc[i]

        # Count consecutive readings above thresholds
        if risk >= crit_threshold:
            consecutive_above_crit += 1
            consecutive_above_warn += 1
        elif risk >= warn_threshold:
            consecutive_above_crit = 0
            consecutive_above_warn += 1
        else:
            consecutive_above_crit = 0
            consecutive_above_warn = 0

        # Determine new state with persistence + hysteresis
        new_state = current_state

        if current_state == "normal":
            if consecutive_above_crit >= persistence:
                new_state = "critical"
            elif consecutive_above_warn >= persistence:
                new_state = "warning"
        elif current_state == "warning":
            if consecutive_above_crit >= persistence:
                new_state = "critical"
            elif risk < (warn_threshold - hysteresis):
                new_state = "normal"
        elif current_state == "critical":
            if risk < (crit_threshold - hysteresis):
                if risk >= warn_threshold:
                    new_state = "warning"
                else:
                    new_state = "normal"

        alerts.iloc[i, alerts.columns.get_loc("alert_level")] = new_state
        alerts.iloc[i, alerts.columns.get_loc("alert_changed")] = (new_state != current_state)
        current_state = new_state

    return alerts


def get_risk_breakdown(row: pd.Series) -> dict:
    """Get per-sensor contribution to the risk index (for interpretability)."""
    breakdown = {}
    for sensor, weight in RISK_WEIGHTS.items():
        if sensor in row.index and not pd.isna(row[sensor]):
            score = sensor_deviation_score(row[sensor], sensor)
            breakdown[sensor] = {
                "value": row[sensor],
                "deviation_score": round(score, 1),
                "weight": weight,
                "contribution": round(weight * score, 1),
                "unit": THRESHOLDS.get(sensor, {}).get("unit", ""),
                "safe_range": f"{THRESHOLDS[sensor]['low']}-{THRESHOLDS[sensor]['high']}" if sensor in THRESHOLDS else "N/A",
            }
    return breakdown


if __name__ == "__main__":
    from config import DATA_SYNTH
    df = pd.read_parquet(DATA_SYNTH / "all_sites.parquet")
    site = df[df["site"] == "WTP_Outlet"].head(500)
    risk = compute_risk_series(site)
    alerts = apply_alert_logic(risk)
    print(f"Risk stats: mean={risk.mean():.1f}, max={risk.max():.1f}")
    print(f"Alerts: {alerts['alert_level'].value_counts().to_dict()}")
