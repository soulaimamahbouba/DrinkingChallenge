"""
AquaGuard – Real-time Urban Drinking Water Quality Monitor
Central configuration for all modules.
"""
from pathlib import Path

# ── Paths ───────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent
DATA_RAW = ROOT / "data" / "raw"
DATA_SYNTH = ROOT / "data" / "synthetic"
MODEL_DIR = ROOT / "models"

# ── Sensor columns (mapped from Kaggle → realistic names) ───
# Original CSV columns → domain-appropriate sensor names
SENSOR_MAP = {
    "ph": "ph",
    "Hardness": "hardness",
    "Solids": "tds",            # total dissolved solids (mg/L)
    "Chloramines": "chloramine", # mg/L
    "Sulfate": "sulfate",
    "Conductivity": "conductivity",  # µS/cm
    "Organic_carbon": "organic_carbon",  # mg/L (TOC proxy)
    "Trihalomethanes": "thm",   # µg/L
    "Turbidity": "turbidity",   # NTU
}

SENSOR_COLS = list(SENSOR_MAP.values())
TARGET_COL = "potability"

# ── Synthetic stream config ─────────────────────────────
SITES = ["WTP_Outlet", "Reservoir_A", "Zone_North", "Zone_South", "EndPoint_1"]
SAMPLE_INTERVAL_MIN = 5        # sensor reading every 5 minutes
STREAM_DAYS = 30               # 30 days of synthetic history

# ── Regulatory thresholds (WHO / EPA guidelines) ────────
THRESHOLDS = {
    "ph":              {"low": 6.5, "high": 8.5,  "unit": "pH"},
    "turbidity":       {"low": 0,   "high": 4.0,  "unit": "NTU"},
    "chloramine":      {"low": 0.2, "high": 4.0,  "unit": "mg/L"},
    "conductivity":    {"low": 0,   "high": 800,  "unit": "µS/cm"},
    "tds":             {"low": 0,   "high": 500,  "unit": "mg/L"},   # approx
    "thm":             {"low": 0,   "high": 80,   "unit": "µg/L"},
    "organic_carbon":  {"low": 0,   "high": 4.0,  "unit": "mg/L"},
    "sulfate":         {"low": 0,   "high": 250,  "unit": "mg/L"},
    "hardness":        {"low": 0,   "high": 300,  "unit": "mg/L CaCO₃"},
}

# ── Risk Index weights (domain-driven) ─────────────────
# Higher weight → more critical for public health
RISK_WEIGHTS = {
    "chloramine": 0.22,   # disinfectant loss = immediate risk
    "turbidity":  0.20,   # pathogen surrogate
    "thm":        0.15,   # DBP carcinogen
    "ph":         0.12,   # corrosion / scaling indicator
    "conductivity": 0.10, # contamination proxy
    "organic_carbon": 0.08,
    "tds":        0.05,
    "sulfate":    0.04,
    "hardness":   0.04,
}

# ── Alerting config ────────────────────────────────────
ALERT_RISK_THRESHOLD = 65       # risk score above this → warning
ALERT_CRITICAL_THRESHOLD = 80   # critical
ALERT_PERSISTENCE_MIN = 3       # consecutive readings above threshold
ALERT_HYSTERESIS = 5            # risk must drop this far below threshold to clear

# ── Model config ───────────────────────────────────────
WINDOW_SIZES = [6, 12, 36, 72]  # rolling-window sizes (readings) = 30min, 1h, 3h, 6h
FORECAST_HORIZON = 12           # predict 1 hour ahead (12 × 5 min)
LGBM_PARAMS = {
    "objective": "binary",
    "metric": "auc",
    "num_leaves": 63,
    "learning_rate": 0.05,
    "feature_fraction": 0.8,
    "bagging_fraction": 0.8,
    "bagging_freq": 5,
    "verbose": -1,
    "n_estimators": 500,
    "early_stopping_rounds": 30,
}

# ── Cause classes ──────────────────────────────────────
CAUSE_CLASSES = [
    "normal",
    "disinfectant_decay",
    "contamination_intrusion",
    "pipe_corrosion",
    "stagnation",
    "operational_change",
    "sensor_fault",
]
