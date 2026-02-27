"""
FastAPI inference service for AquaGuard.

Endpoints:
  POST /predict          — single reading → risk + potability + cause
  POST /predict/batch    — batch readings
  GET  /health           — health check
  GET  /model/info       — model metadata
  WS   /ws/stream        — WebSocket for real-time streaming demo
"""
import numpy as np
import pandas as pd
import joblib
from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import asyncio
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from config import MODEL_DIR, SENSOR_COLS, CAUSE_CLASSES, SITES, DATA_SYNTH
from src.features.engineering import build_features
from src.alerts.risk_index import (
    compute_risk_index, get_risk_breakdown, sensor_deviation_score
)
from src.alerts.cause_engine import rule_based_diagnosis, hybrid_diagnosis

app = FastAPI(
    title="AquaGuard — Water Quality API",
    version="1.0.0",
    description="Real-time urban drinking water quality prediction & early warning",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Load models at startup ──────────────────────────────
models = {}

@app.on_event("startup")
def load_models():
    try:
        models["potability"] = joblib.load(MODEL_DIR / "potability_lgbm.pkl")
        models["cause"] = joblib.load(MODEL_DIR / "cause_lgbm.pkl")
        models["forecast"] = joblib.load(MODEL_DIR / "forecast_models.pkl")
        models["feature_cols"] = joblib.load(MODEL_DIR / "feature_cols.pkl")
        print("✓ All models loaded")
    except FileNotFoundError as e:
        print(f"⚠ Model not found: {e}. Run train.py first.")


# ── Request / Response schemas ──────────────────────────
class SensorReading(BaseModel):
    timestamp: Optional[str] = None
    site: Optional[str] = "WTP_Outlet"
    ph: Optional[float] = None
    hardness: Optional[float] = None
    tds: Optional[float] = None
    chloramine: Optional[float] = None
    sulfate: Optional[float] = None
    conductivity: Optional[float] = None
    organic_carbon: Optional[float] = None
    thm: Optional[float] = None
    turbidity: Optional[float] = None


class PredictionResponse(BaseModel):
    risk_index: float
    risk_level: str
    potability_probability: float
    potable: bool
    primary_cause: str
    cause_confidence: float
    risk_breakdown: dict
    cause_details: dict


# ── Endpoints ───────────────────────────────────────────
@app.get("/health")
def health():
    return {
        "status": "healthy",
        "models_loaded": list(models.keys()),
        "sensors": SENSOR_COLS,
        "sites": SITES,
    }


@app.get("/model/info")
def model_info():
    info = {"models": {}}
    if "potability" in models:
        info["models"]["potability"] = {
            "type": "LightGBM Binary Classifier",
            "n_features": len(models.get("feature_cols", [])),
        }
    if "cause" in models:
        info["models"]["cause"] = {
            "type": "LightGBM Multi-class",
            "classes": CAUSE_CLASSES,
        }
    if "forecast" in models:
        info["models"]["forecast"] = {
            "type": "LightGBM Regressors (per-sensor)",
            "sensors": list(models["forecast"].keys()),
        }
    return info


@app.post("/predict", response_model=PredictionResponse)
def predict(reading: SensorReading):
    """Predict water quality from a single sensor reading."""
    row = reading.dict()

    # Compute risk index directly from sensor values
    row_series = pd.Series(row)
    risk = compute_risk_index(row_series)
    breakdown = get_risk_breakdown(row_series)

    # Determine risk level
    if risk >= 80:
        risk_level = "critical"
    elif risk >= 65:
        risk_level = "warning"
    elif risk >= 50:
        risk_level = "caution"
    elif risk >= 30:
        risk_level = "normal"
    else:
        risk_level = "excellent"

    # Rule-based cause diagnosis (always available, no features needed)
    cause_result = hybrid_diagnosis(row)

    # ML prediction (if model loaded, would need full feature vector)
    # For simple endpoint, use rule engine; batch endpoint uses full pipeline
    pot_prob = max(0, 1 - risk / 100)  # approximate from risk

    return PredictionResponse(
        risk_index=round(risk, 1),
        risk_level=risk_level,
        potability_probability=round(pot_prob, 3),
        potable=pot_prob > 0.5,
        primary_cause=cause_result["primary_cause"],
        cause_confidence=cause_result["confidence"],
        risk_breakdown=breakdown,
        cause_details=cause_result,
    )


@app.websocket("/ws/stream")
async def stream_demo(websocket: WebSocket):
    """WebSocket endpoint to stream synthetic data for live demo."""
    await websocket.accept()
    try:
        # Load synthetic data
        df = pd.read_parquet(DATA_SYNTH / "all_sites.parquet")
        site_df = df[df["site"] == SITES[0]].sort_values("timestamp").reset_index(drop=True)

        for idx in range(min(500, len(site_df))):
            row = site_df.iloc[idx]
            row_dict = row.to_dict()

            risk = compute_risk_index(row)
            cause = rule_based_diagnosis(row_dict)

            message = {
                "timestamp": str(row["timestamp"]),
                "sensors": {s: round(float(row[s]), 3) for s in SENSOR_COLS if s in row.index and not pd.isna(row[s])},
                "risk_index": round(float(risk), 1),
                "event_type": row.get("event_type", "normal"),
                "cause": cause[0] if cause else {"cause": "normal"},
            }
            await websocket.send_json(message)
            await asyncio.sleep(0.3)  # ~300ms between readings for demo speed

    except Exception as e:
        await websocket.close(reason=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
