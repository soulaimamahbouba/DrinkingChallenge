"""
Probable cause identification — hybrid ML + rule-based.

Combines:
1. LightGBM multi-class cause classifier (trained in models/train.py)
2. Domain-expert rule engine for explainability
3. SHAP values for tree model interpretability
4. Sensor residual analysis (actual vs. forecast → anomaly direction)
"""
import numpy as np
import pandas as pd
import joblib
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from config import MODEL_DIR, CAUSE_CLASSES, SENSOR_COLS, THRESHOLDS


# ── Rule engine ─────────────────────────────────────────
RULES = [
    {
        "cause": "disinfectant_decay",
        "conditions": lambda r: (
            r.get("chloramine", 99) < THRESHOLDS["chloramine"]["low"] * 1.5
            and r.get("thm", 0) > THRESHOLDS["thm"]["high"] * 0.7
        ),
        "confidence": 0.85,
        "explanation": "Chloramine below safe threshold + THM rising → disinfection breakdown",
    },
    {
        "cause": "contamination_intrusion",
        "conditions": lambda r: (
            r.get("turbidity", 0) > THRESHOLDS["turbidity"]["high"] * 0.8
            and r.get("conductivity", 0) > THRESHOLDS["conductivity"]["high"] * 0.6
        ),
        "confidence": 0.80,
        "explanation": "Turbidity spike + conductivity jump → possible pipe break / intrusion",
    },
    {
        "cause": "pipe_corrosion",
        "conditions": lambda r: (
            r.get("ph", 7) < THRESHOLDS["ph"]["low"]
            and r.get("hardness", 0) > 220
        ),
        "confidence": 0.75,
        "explanation": "Low pH + elevated hardness → pipe corrosion / metal leaching",
    },
    {
        "cause": "stagnation",
        "conditions": lambda r: (
            r.get("chloramine", 99) < THRESHOLDS["chloramine"]["low"] * 2.0
            and r.get("turbidity_diff1", 0) > 0  # slowly rising
            and r.get("chloramine_diff1", 0) < 0  # slowly falling
        ),
        "confidence": 0.70,
        "explanation": "Gradual chloramine decay + slight turbidity rise → stagnation in dead-end pipe",
    },
    {
        "cause": "sensor_fault",
        "conditions": lambda r: (
            r.get("ph_stuck", 0) == 1
            or r.get("conductivity_stuck", 0) == 1
            or r.get("chloramine_stuck", 0) == 1
        ),
        "confidence": 0.90,
        "explanation": "Zero variance detected on sensor → stuck/faulty sensor reading",
    },
    {
        "cause": "operational_change",
        "conditions": lambda r: (
            abs(r.get("chloramine_diff3", 0)) > 1.5
            and r.get("turbidity", 0) < THRESHOLDS["turbidity"]["high"]
        ),
        "confidence": 0.65,
        "explanation": "Sudden chloramine shift without turbidity change → treatment dosing change",
    },
]


def rule_based_diagnosis(row: dict) -> list:
    """
    Run all rules against a sensor reading.
    Returns list of {cause, confidence, explanation} sorted by confidence.
    """
    hits = []
    for rule in RULES:
        try:
            if rule["conditions"](row):
                hits.append({
                    "cause": rule["cause"],
                    "confidence": rule["confidence"],
                    "explanation": rule["explanation"],
                    "method": "rule",
                })
        except (KeyError, TypeError):
            continue
    return sorted(hits, key=lambda x: x["confidence"], reverse=True)


def ml_based_diagnosis(features: np.ndarray, model=None) -> list:
    """
    Use the trained cause classifier for diagnosis.
    Returns list of {cause, confidence} for top predictions.
    """
    if model is None:
        try:
            model = joblib.load(MODEL_DIR / "cause_lgbm.pkl")
        except FileNotFoundError:
            return []

    proba = model.predict_proba(features.reshape(1, -1))[0]
    results = []
    for i, p in enumerate(proba):
        if p > 0.1:  # Only report causes with >10% probability
            results.append({
                "cause": CAUSE_CLASSES[i],
                "confidence": round(float(p), 3),
                "method": "ml_classifier",
            })
    return sorted(results, key=lambda x: x["confidence"], reverse=True)


def get_shap_explanation(features: np.ndarray, feature_names: list, model=None, top_n=5):
    """
    Get SHAP-based feature explanations for the cause prediction.
    Returns top contributing features.
    """
    try:
        import shap
        if model is None:
            model = joblib.load(MODEL_DIR / "cause_lgbm.pkl")
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(features.reshape(1, -1))

        # For the predicted class
        pred_class = model.predict(features.reshape(1, -1))[0]
        if isinstance(shap_values, list):
            sv = shap_values[pred_class][0]
        else:
            sv = shap_values[0]

        top_indices = np.argsort(np.abs(sv))[-top_n:][::-1]
        explanations = []
        for idx in top_indices:
            explanations.append({
                "feature": feature_names[idx],
                "shap_value": round(float(sv[idx]), 4),
                "feature_value": round(float(features[idx]), 4),
                "direction": "increases risk" if sv[idx] > 0 else "decreases risk",
            })
        return explanations
    except ImportError:
        return [{"note": "SHAP not installed — install with: pip install shap"}]
    except Exception as e:
        return [{"note": f"SHAP error: {str(e)}"}]


def hybrid_diagnosis(row_dict: dict, features: np.ndarray = None,
                     feature_names: list = None, cause_model=None) -> dict:
    """
    Combined diagnosis: merge rule hits + ML predictions.
    Returns final diagnosis with explanation.
    """
    # 1. Rule-based
    rule_hits = rule_based_diagnosis(row_dict)

    # 2. ML-based
    ml_hits = []
    if features is not None:
        ml_hits = ml_based_diagnosis(features, cause_model)

    # 3. Merge: boost confidence when both agree
    final_scores = {}
    for hit in rule_hits:
        cause = hit["cause"]
        final_scores[cause] = final_scores.get(cause, 0) + hit["confidence"] * 0.5

    for hit in ml_hits:
        cause = hit["cause"]
        final_scores[cause] = final_scores.get(cause, 0) + hit["confidence"] * 0.5

    if not final_scores:
        return {
            "primary_cause": "normal",
            "confidence": 1.0,
            "explanations": [{"note": "All parameters within expected ranges"}],
            "rule_hits": [],
            "ml_predictions": [],
        }

    # Sort by combined score
    ranked = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)
    primary_cause = ranked[0][0]
    primary_conf = min(ranked[0][1], 1.0)

    # Get SHAP explanation for top cause
    shap_expl = []
    if features is not None and feature_names is not None:
        shap_expl = get_shap_explanation(features, feature_names, cause_model)

    # Get rule explanation
    rule_explanations = [h["explanation"] for h in rule_hits if h["cause"] == primary_cause]

    return {
        "primary_cause": primary_cause,
        "confidence": round(primary_conf, 3),
        "all_causes": [{
            "cause": c,
            "score": round(s, 3)
        } for c, s in ranked],
        "rule_explanations": rule_explanations,
        "shap_explanations": shap_expl,
        "rule_hits": rule_hits,
        "ml_predictions": ml_hits,
    }
