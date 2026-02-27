# AquaGuard 💧

**Real-time Urban Drinking Water Quality Degradation Prediction, Early Warning & Probable Cause Identification**

> AI Night Challenge 2026

## Quick Start (3 commands)

```bash
pip install -r requirements.txt
python run.py demo
```

This will: generate synthetic sensor data → train models → launch the Streamlit dashboard.

## Architecture

```
Sensors (5-min interval) → Ingestion → Validation → Feature Engineering → ML Inference
                                                            ↓
                                              Risk Index (0-100) → Alert Engine → Dashboard
                                                            ↓
                                              Cause Classifier → Root Cause Panel
```

## Project Structure

```
DrinkingChallenge/
├── config.py                    # Central configuration
├── run.py                       # One-click runner
├── requirements.txt
├── data/
│   ├── raw/                     # Original Kaggle CSV
│   └── synthetic/               # Generated time-series (parquet)
├── models/                      # Trained model artifacts
├── src/
│   ├── data/
│   │   └── synthetic_generator.py   # Temporal data synthesis + event injection
│   ├── features/
│   │   └── engineering.py           # Rolling stats, EWMA, derivatives, lags
│   ├── models/
│   │   └── train.py                 # LightGBM potability + cause + forecast
│   ├── alerts/
│   │   ├── risk_index.py            # WQRI score (0-100) + alert state machine
│   │   └── cause_engine.py          # Hybrid ML + rule-based diagnosis
│   ├── api/
│   │   └── server.py               # FastAPI inference endpoints + WebSocket
│   └── dashboard/
│       └── app.py                   # Streamlit real-time monitoring UI
├── notebooks/                   # EDA & evaluation notebooks
└── docs/                        # Technical documentation
```

## Components

| Module | Purpose |
|--------|---------|
| **Synthetic Generator** | Converts static CSV → 30-day multi-site sensor streams with injected events |
| **Feature Engineering** | 200+ features: rolling stats, EWMA, derivatives, lags, cyclical time, cross-sensor ratios |
| **Potability Model** | LightGBM binary classifier — "will water be non-potable in ~1hr?" |
| **Cause Classifier** | LightGBM multi-class — 7 cause categories |
| **Forecast Models** | Per-sensor regressors for anomaly scoring via residuals |
| **Risk Index (WQRI)** | Weighted composite score with EWMA smoothing |
| **Alert Engine** | Stateful: persistence + hysteresis to minimize false alarms |
| **Cause Engine** | Hybrid: ML classifier + domain rule engine + SHAP explanations |
| **Dashboard** | 5-tab Streamlit app: risk overview, sensor trends, alerts, root cause, data |

## License

MIT — built for AI Night Challenge demonstration purposes.
