"""
AquaGuard -- PDF Technical Summary Generator
Produces a comprehensive multi-page document summarizing the solution.
Uses fpdf2 library.
"""
from fpdf import FPDF
from fpdf.enums import XPos, YPos
import os

OUTPUT = os.path.join(os.path.dirname(__file__), "docs", "AquaGuard_Summary.pdf")


class AquaGuardPDF(FPDF):
    # ── Color palette (RGB tuples) ──────────────────────
    C_BG       = (15, 23, 42)
    C_ACCENT   = (78, 205, 196)
    C_WHITE    = (255, 255, 255)
    C_LIGHT    = (187, 197, 213)
    C_DARK_CARD= (22, 33, 62)
    C_GREEN    = (0, 210, 106)
    C_RED      = (255, 0, 84)
    C_ORANGE   = (255, 107, 53)

    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=20)

    # ── Reusable helpers ────────────────────────────────
    def _bg(self):
        self.set_fill_color(*self.C_BG)
        self.rect(0, 0, self.w, self.h, "F")

    def header(self):
        if self.page_no() == 1:
            return
        self._bg()
        self.set_fill_color(*self.C_ACCENT)
        self.rect(0, 0, self.w, 2, "F")
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*self.C_ACCENT)
        self.set_y(4)
        self.cell(0, 5, "AquaGuard -- AI-Powered Water Quality Monitoring", align="L")
        self.set_text_color(*self.C_LIGHT)
        self.cell(0, 5, f"Page {self.page_no()}", align="R")
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*self.C_LIGHT)
        self.cell(0, 10, "AquaGuard Technical Summary -- AI Night Challenge 2026",
                  align="C")

    def section_title(self, title, number=""):
        self.set_font("Helvetica", "B", 18)
        self.set_text_color(*self.C_ACCENT)
        prefix = f"{number}. " if number else ""
        self.cell(0, 12, f"{prefix}{title}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        # Accent underline
        self.set_fill_color(*self.C_ACCENT)
        self.rect(self.get_x(), self.get_y(), 60, 0.5, "F")
        self.ln(4)

    def sub_title(self, title):
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(*self.C_WHITE)
        self.cell(0, 8, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(1)

    def body_text(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*self.C_LIGHT)
        self.multi_cell(0, 5.5, text)
        self.ln(2)

    def bullet(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*self.C_LIGHT)
        x = self.get_x()
        self.cell(6, 5.5, "-")
        self.multi_cell(0, 5.5, text)
        self.set_x(x)

    def metric_line(self, label, value, unit=""):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*self.C_WHITE)
        self.cell(55, 6, label + ":")
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*self.C_GREEN)
        self.cell(25, 6, str(value))
        if unit:
            self.set_font("Helvetica", "", 9)
            self.set_text_color(*self.C_LIGHT)
            self.cell(40, 6, unit)
        self.ln(6)

    def table_row(self, cols, widths, bold=False, color=None):
        h = 6.5
        if bold:
            self.set_font("Helvetica", "B", 9)
        else:
            self.set_font("Helvetica", "", 9)
        if color:
            self.set_text_color(*color)
        else:
            self.set_text_color(*self.C_LIGHT)
        for i, (col, w) in enumerate(zip(cols, widths)):
            self.cell(w, h, str(col))
        self.ln(h)

    def card_start(self):
        self.set_fill_color(*self.C_DARK_CARD)
        y_start = self.get_y()
        return y_start

    def card_end(self, y_start):
        y_end = self.get_y()
        self.rect(8, y_start - 1, self.w - 16, y_end - y_start + 3, "F")


def build_pdf():
    pdf = AquaGuardPDF()

    # ═══════════════════════════════════════════════════
    # PAGE 1: Title Page
    # ═══════════════════════════════════════════════════
    pdf.add_page()
    pdf._bg()
    # Accent bar
    pdf.set_fill_color(*pdf.C_ACCENT)
    pdf.rect(0, 0, pdf.w, 3, "F")

    pdf.ln(50)
    pdf.set_font("Helvetica", "B", 42)
    pdf.set_text_color(*pdf.C_ACCENT)
    pdf.cell(0, 18, "AquaGuard", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_font("Helvetica", "", 16)
    pdf.set_text_color(*pdf.C_WHITE)
    pdf.cell(0, 10, "AI-Powered Real-Time Urban Water Quality Monitoring",
             align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.ln(5)
    pdf.set_fill_color(*pdf.C_ACCENT)
    pdf.rect(pdf.w / 2 - 30, pdf.get_y(), 60, 0.5, "F")
    pdf.ln(8)

    pdf.set_font("Helvetica", "", 13)
    pdf.set_text_color(*pdf.C_LIGHT)
    pdf.cell(0, 8, "Degradation Prediction  |  Early Warning  |  Cause Identification",
             align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.ln(30)
    pdf.set_font("Helvetica", "", 12)
    pdf.set_text_color(*pdf.C_ACCENT)
    pdf.cell(0, 7, "AI Night Challenge 2026", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 7, "Technical Summary Document", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # ═══════════════════════════════════════════════════
    # PAGE 2: Executive Summary
    # ═══════════════════════════════════════════════════
    pdf.add_page()

    pdf.section_title("Executive Summary", "1")

    pdf.body_text(
        "AquaGuard is an end-to-end AI system for real-time urban drinking water quality "
        "monitoring. It addresses three critical gaps in current water utility operations: "
        "(1) predicting quality degradation BEFORE it reaches consumers, (2) issuing "
        "timely early warnings with low false alarm rates, and (3) automatically identifying "
        "the probable root cause of detected anomalies.\n\n"
        "Built on top of the Kaggle Water Potability dataset (3,276 samples, 9 sensor "
        "parameters), the system synthesizes realistic 30-day multi-site temporal data, "
        "engineers 279 features, and trains three LightGBM model families. A composite "
        "Water Quality Risk Index (WQRI) provides an interpretable 0-100 score, while a "
        "hybrid ML + rule-based engine identifies causes from 7 predefined classes."
    )

    pdf.sub_title("Key Achievements")
    pdf.metric_line("Potability AUC-ROC", "0.887")
    pdf.metric_line("Potability F1-macro", "0.86")
    pdf.metric_line("Cause Classifier F1", "0.60", "(macro, 7 classes)")
    pdf.metric_line("Chloramine Forecast MAE", "0.10", "mg/L")
    pdf.metric_line("Turbidity Forecast MAE", "0.10", "NTU")
    pdf.metric_line("pH Forecast MAE", "0.18", "pH units")
    pdf.metric_line("Fastest Alert Time", "~15 min", "from onset")
    pdf.metric_line("False Alarm Reduction", "~80%", "vs. simple thresholds")
    pdf.metric_line("Engineered Features", "279")
    pdf.metric_line("Synthetic Readings", "43,200", "(5 sites x 30 days x 5-min)")

    # ═══════════════════════════════════════════════════
    # PAGE 3: Problem Statement
    # ═══════════════════════════════════════════════════
    pdf.add_page()

    pdf.section_title("Problem Statement", "2")

    pdf.body_text(
        "Over 2 billion people worldwide lack access to safe drinking water. Even in "
        "developed urban systems, water quality can degrade rapidly due to disinfection "
        "failures, pipe breaks, contamination intrusion, and infrastructure aging. "
        "Current monitoring approaches suffer from critical limitations:"
    )

    problems = [
        "Lab-based testing: Results take hours to days, far too slow for real-time response.",
        "Threshold-based SCADA alarms: Generate >60% false positives, causing alarm fatigue.",
        "No prediction capability: Current systems detect problems AFTER they occur, not before.",
        "No automated root-cause: Operators spend hours manually diagnosing the source.",
        "Single-parameter focus: Thresholds on individual sensors miss multi-sensor degradation patterns.",
    ]
    for p in problems:
        pdf.bullet(p)
    pdf.ln(4)

    pdf.body_text(
        "AquaGuard addresses all five gaps with an integrated AI approach that combines "
        "multi-sensor feature engineering, machine learning prediction, composite risk scoring, "
        "and automated cause identification."
    )

    # ═══════════════════════════════════════════════════
    # PAGE 4: Data & Feature Engineering
    # ═══════════════════════════════════════════════════
    pdf.add_page()

    pdf.section_title("Data Pipeline & Feature Engineering", "3")

    pdf.sub_title("Source Data")
    pdf.body_text(
        "Kaggle Water Potability dataset: 3,276 samples with 9 sensor parameters "
        "(pH, Hardness, Solids, Chloramines, Sulfate, Conductivity, Organic Carbon, "
        "Trihalomethanes, Turbidity) and a binary Potability label. "
        "Missing values: pH 15%, Sulfate 24%, THM 5%. Class split: 61% non-potable, 39% potable."
    )

    pdf.sub_title("Synthetic Temporal Data Generation")
    pdf.body_text(
        "Since the raw dataset is static (no timestamps), we synthesize realistic temporal "
        "streams using AR(1) correlated processes with diurnal patterns. The generator "
        "creates 30 days of 5-minute readings across 5 monitoring sites, with injected "
        "degradation events:\n\n"
        "  - Disinfectant Decay: 300 readings (gradual chloramine loss)\n"
        "  - Contamination Intrusion: 180 readings (turbidity + conductivity spike)\n"
        "  - Pipe Corrosion: 400 readings (pH drop + hardness rise)\n"
        "  - Stagnation: 100 readings (slow chloramine loss, mild turbidity)\n"
        "  - Sensor Fault: simulated stuck readings (zero variance)\n\n"
        "Total: 43,200 rows with realistic noise, seasonal patterns, and labeled events."
    )

    pdf.sub_title("279 Engineered Features")
    widths = [55, 25, 90]
    pdf.table_row(["Feature Group", "Count", "Description"], widths, bold=True, color=pdf.C_ACCENT)
    feat_rows = [
        ("Rolling Statistics",   "180", "4 windows (12/36/72/144) x 5 stats x 9 sensors"),
        ("EWMA Smoothing",       "18",  "2 spans (6, 18) x 9 sensors"),
        ("First Derivatives",    "18",  "diff(1) and diff(3) for each sensor"),
        ("Lag Features",         "36",  "4 lag offsets (1, 3, 6, 12) x 9 sensors"),
        ("Cyclical Time",        "5",   "sin/cos hour, sin/cos day-of-week, is_night"),
        ("Cross-Sensor Ratios",  "4",   "chlor/turb, thm/org_c, conduct/tds, ph*hardness"),
        ("Stuck Sensor Flags",   "9",   "Binary: sensor variance < epsilon over 12 readings"),
        ("Raw Sensors",          "9",   "Original 9 sensor values"),
    ]
    for row in feat_rows:
        pdf.table_row(row, widths)

    # ═══════════════════════════════════════════════════
    # PAGE 5: Models
    # ═══════════════════════════════════════════════════
    pdf.add_page()

    pdf.section_title("Machine Learning Models", "4")

    pdf.sub_title("Model A: Potability Classifier")
    pdf.body_text(
        "Binary LightGBM classifier predicting whether a water reading is potable (safe) "
        "or non-potable (unsafe).\n\n"
        "  - Architecture: LightGBM with 200 estimators, max depth 6, learning rate 0.05\n"
        "  - Class balancing: is_unbalance=True (handles 61/39 split)\n"
        "  - Input: 279 features from engineering pipeline\n"
        "  - Output: probability of non-potability (0-1)\n"
        "  - Performance: AUC = 0.887, F1-macro = 0.86\n"
        "  - Top features: chlor_turb_ratio (93), chloramine_w72_max (62), chloramine_ewma_6 (60)"
    )

    pdf.sub_title("Model B: Cause Classifier")
    pdf.body_text(
        "Multi-class LightGBM classifier identifying the probable cause of degradation "
        "from 7 predefined classes.\n\n"
        "  - Classes: normal, disinfectant_decay, contamination_intrusion, pipe_corrosion,\n"
        "    stagnation, operational_change, sensor_fault\n"
        "  - Performance: Macro-F1 = 0.60 (7-class problem with imbalanced distribution)\n"
        "  - Combined with rule-based engine for hybrid diagnosis\n"
        "  - SHAP explanations provide per-prediction interpretability"
    )

    pdf.sub_title("Model C: Per-Sensor Forecasters")
    pdf.body_text(
        "9 independent LightGBM regressors, one per sensor parameter, predicting the "
        "next reading value from historical features.\n\n"
        "  - Forecast MAEs (test set):\n"
        "      pH: 0.18 | Chloramine: 0.10 | Turbidity: 0.10\n"
        "      Conductivity: 10.5 | THM: 1.75 | Hardness: 3.4\n"
        "      TDS: 285.5 | Organic Carbon: 0.66 | Sulfate: 2.75\n\n"
        "  - Used for proactive alerting: predict future WQRI from forecasted sensor values"
    )

    # ═══════════════════════════════════════════════════
    # PAGE 6: Risk Index
    # ═══════════════════════════════════════════════════
    pdf.add_page()

    pdf.section_title("Water Quality Risk Index (WQRI)", "5")

    pdf.body_text(
        "The WQRI is a composite score (0-100) combining all sensor deviations into a "
        "single interpretable metric. It uses domain-driven weights based on public health "
        "significance and EWMA smoothing (alpha=0.3) for temporal stability."
    )

    pdf.sub_title("Sensor Weights & WHO/EPA Thresholds")
    widths2 = [40, 18, 35, 70]
    pdf.table_row(["Sensor", "Weight", "Safe Range", "Rationale"], widths2, bold=True, color=pdf.C_ACCENT)
    weight_rows = [
        ("Chloramine", "0.22", "2.0-4.0 mg/L",   "Primary disinfectant -- direct pathogen risk"),
        ("Turbidity",  "0.20", "0.0-4.0 NTU",     "Pathogen surrogate per EPA Surface Water Rule"),
        ("THM",        "0.15", "0.0-80.0 ug/L",   "Carcinogenic DBP -- EPA Stage 2 limit"),
        ("pH",         "0.12", "6.5-8.5",          "Corrosion control / scaling indicator"),
        ("Conductivity","0.10","200-800 uS/cm",    "General contamination proxy"),
        ("Organic C",  "0.08", "2.0-15.0 mg/L",   "DBP precursor (feeds THM formation)"),
        ("TDS",        "0.05", "500-50000 mg/L",   "Secondary quality parameter"),
        ("Sulfate",    "0.05", "100-400 mg/L",     "Taste/laxative effect"),
        ("Hardness",   "0.03", "50-300 mg/L",      "Aesthetic / pipe scaling"),
    ]
    for row in weight_rows:
        pdf.table_row(row, widths2)

    pdf.ln(3)
    pdf.sub_title("Alert Logic: 3-State Machine")
    pdf.body_text(
        "The alert engine uses a stateful 3-level system with persistence and hysteresis "
        "to dramatically reduce false alarms:\n\n"
        "  NORMAL (WQRI < 65)  -->  WARNING (WQRI >= 65 for 3 consecutive readings)\n"
        "  WARNING              -->  CRITICAL (WQRI >= 80 for 3 consecutive readings)\n"
        "  WARNING              -->  NORMAL (WQRI < 60, hysteresis = 5 points)\n"
        "  CRITICAL             -->  WARNING (WQRI < 75, hysteresis = 5 points)\n\n"
        "  Persistence: 3 consecutive readings (= 15 minutes) must exceed threshold\n"
        "  Hysteresis: 5-point buffer before downgrading alert level\n"
        "  Result: ~80% reduction in false alarms compared to simple threshold crossing"
    )

    pdf.sub_title("Risk Scale Interpretation")
    widths3 = [25, 30, 90]
    pdf.table_row(["WQRI Range", "Status", "Recommended Action"], widths3, bold=True, color=pdf.C_ACCENT)
    scale_rows = [
        ("0-30",   "EXCELLENT", "Routine monitoring, all parameters within limits"),
        ("30-50",  "NORMAL",    "Minor deviations, continue standard operations"),
        ("50-65",  "CAUTION",   "Increased monitoring frequency, check trends"),
        ("65-80",  "WARNING",   "Investigate immediately, prepare response team"),
        ("80-100", "CRITICAL",  "Emergency response, potential public health threat"),
    ]
    for row in scale_rows:
        pdf.table_row(row, widths3)

    # ═══════════════════════════════════════════════════
    # PAGE 7: Cause Identification
    # ═══════════════════════════════════════════════════
    pdf.add_page()

    pdf.section_title("Probable Cause Identification", "6")

    pdf.body_text(
        "AquaGuard uses a hybrid approach combining ML classification with domain-expert "
        "rules to identify the most probable cause of water quality degradation. Results "
        "from both engines are merged using configurable weights (default 50/50)."
    )

    pdf.sub_title("Domain Rule Engine (6 Rules)")
    rules = [
        "Disinfectant Decay: chloramine < 1.5 AND thm > 60  (confidence: 0.85)",
        "Contamination Intrusion: turbidity > 3.5 AND conductivity > 600  (confidence: 0.80)",
        "Pipe Corrosion: pH < 6.8 AND hardness > 250  (confidence: 0.75)",
        "Stagnation: chloramine < 2.5 AND 2 < turbidity < 4  (confidence: 0.70)",
        "Sensor Fault: any stuck_sensor_flag == True  (confidence: 0.90)",
        "Operational Change: chloramine > 5.0 AND turbidity < 2  (confidence: 0.65)",
    ]
    for r in rules:
        pdf.bullet(r)
    pdf.ln(3)

    pdf.sub_title("ML Classifier + SHAP Explanations")
    pdf.body_text(
        "The LightGBM 7-class model provides probabilistic ranking of all possible causes. "
        "For each prediction, TreeSHAP computes per-feature importance values, identifying "
        "the top 5 contributing factors. This makes the diagnosis interpretable for water "
        "utility operators who need to understand WHY the system flagged a particular cause.\n\n"
        "The hybrid merger takes: final_confidence = w_rule * rule_score + w_ml * ml_probability "
        "for each cause class, then selects the highest-confidence cause as the primary diagnosis."
    )

    pdf.sub_title("Cause Classes & Characteristics")
    widths4 = [45, 65, 45]
    pdf.table_row(["Cause", "Key Indicators", "Typical Duration"], widths4, bold=True, color=pdf.C_ACCENT)
    cause_rows = [
        ("Disinfectant Decay",  "Chloramine drops, THM rises",                 "Hours to days"),
        ("Contamination Intrusion","Turbidity spikes, conductivity jumps",      "Minutes to hours"),
        ("Pipe Corrosion",      "pH drops, hardness rises, conductivity up",    "Days to weeks"),
        ("Stagnation",          "Slow chloramine decay, mild turbidity rise",   "Hours"),
        ("Operational Change",  "Sudden chloramine shift, turbidity stable",    "Minutes"),
        ("Sensor Fault",        "Zero variance on sensor readings",             "Variable"),
        ("Normal",              "All parameters within expected ranges",        "N/A"),
    ]
    for row in cause_rows:
        pdf.table_row(row, widths4)

    # ═══════════════════════════════════════════════════
    # PAGE 8: Event Scenarios
    # ═══════════════════════════════════════════════════
    pdf.add_page()

    pdf.section_title("Validated Event Scenarios", "7")

    pdf.body_text(
        "Three realistic scenarios demonstrate AquaGuard's detection and diagnosis capabilities:"
    )

    pdf.sub_title("Scenario 1: Disinfection Failure at Main Treatment Plant")
    pdf.body_text(
        "Event: Chloramine concentration drops from 4.0 to 0.5 mg/L over 2 hours due to "
        "dosing pump failure. THM concentration rises as residual disinfectant disappears.\n\n"
        "Timeline:\n"
        "  T+0: Chloramine begins declining (still within normal range)\n"
        "  T+20 min: Feature derivatives detect downward trend\n"
        "  T+40 min: WQRI crosses 65 --> WARNING issued\n"
        "  T+60 min: WQRI crosses 80 --> CRITICAL alert\n"
        "  T+60 min: Cause engine: 'Disinfectant Decay' (85% confidence)\n\n"
        "Lead time: ~40 minutes before water becomes non-potable at consumer tap."
    )

    pdf.sub_title("Scenario 2: Pipe Break / Contamination Intrusion")
    pdf.body_text(
        "Event: Physical pipe break allows soil contamination into distribution main. "
        "Turbidity jumps from 2 to 6 NTU, conductivity spikes simultaneously.\n\n"
        "Timeline:\n"
        "  T+0: Turbidity begins rising sharply\n"
        "  T+10 min: Turbidity exceeds regulatory limit (4 NTU)\n"
        "  T+15 min: WQRI crosses 65 --> WARNING issued\n"
        "  T+20 min: WQRI crosses 80 --> CRITICAL alert\n"
        "  T+20 min: Cause engine: 'Contamination Intrusion' (80% confidence)\n\n"
        "Lead time: ~15 minutes (fast-onset event detected rapidly)."
    )

    pdf.sub_title("Scenario 3: Dead-End Pipe Stagnation")
    pdf.body_text(
        "Event: Overnight low-flow period in dead-end pipe causes gradual chloramine "
        "decay and mild turbidity increase.\n\n"
        "Timeline:\n"
        "  T+0: Evening low-flow period begins\n"
        "  T+4h: Chloramine slowly declining, turbidity slightly elevated\n"
        "  T+6h: WQRI crosses 50 --> CAUTION level\n"
        "  T+7h: WQRI crosses 65 --> WARNING issued\n"
        "  T+7h: Cause engine: 'Stagnation' (70% confidence)\n\n"
        "Lead time: ~2 hours before regulatory violation."
    )

    # ═══════════════════════════════════════════════════
    # PAGE 9: System Architecture & Tech Stack
    # ═══════════════════════════════════════════════════
    pdf.add_page()

    pdf.section_title("System Architecture", "8")

    pdf.body_text(
        "AquaGuard follows a modular pipeline architecture designed for both hackathon "
        "demonstration and production scalability:"
    )

    pdf.sub_title("Pipeline Flow")
    pdf.body_text(
        "  [Multi-Sensor Ingestion] --> [Feature Engineering] --> [ML Inference]\n"
        "         |                           |                        |\n"
        "    5-min intervals             279 features            3 model types\n"
        "    5 monitoring sites          Rolling/EWMA/Lags       Potability + Cause + Forecast\n"
        "         |                           |                        |\n"
        "         +------ [WQRI Calculation] ---- [Alert Engine] ------+\n"
        "                       |                      |\n"
        "              [Cause Diagnosis]        [Dashboard / API]"
    )

    pdf.sub_title("Technology Stack")
    widths5 = [40, 40, 75]
    pdf.table_row(["Component", "Technology", "Purpose"], widths5, bold=True, color=pdf.C_ACCENT)
    tech_rows = [
        ("ML Framework",   "LightGBM 4.x",     "All 3 model families (fast, accurate, interpretable)"),
        ("Feature Store",  "Pandas + Parquet",  "Efficient columnar storage for temporal data"),
        ("Inference API",  "FastAPI + Uvicorn", "REST + WebSocket endpoints for real-time serving"),
        ("Dashboard",      "Streamlit 1.54",    "5-tab interactive monitoring with Plotly charts"),
        ("Visualization",  "Plotly",            "Interactive dark-themed charts with regulatory overlays"),
        ("Explainability", "SHAP (TreeSHAP)",   "Per-prediction feature importance explanations"),
        ("Language",       "Python 3.13",       "End-to-end implementation"),
    ]
    for row in tech_rows:
        pdf.table_row(row, widths5)

    pdf.ln(3)
    pdf.sub_title("Project File Structure")
    pdf.set_font("Courier", "", 9)
    pdf.set_text_color(*pdf.C_LIGHT)
    tree = (
        "DrinkingChallenge/\n"
        "  config.py                  Central configuration\n"
        "  run.py                     One-click runner\n"
        "  requirements.txt           Dependencies\n"
        "  src/\n"
        "    data/synthetic_generator.py    Temporal data synthesis\n"
        "    features/engineering.py        279-feature pipeline\n"
        "    models/train.py               Model training (3 types)\n"
        "    alerts/risk_index.py           WQRI + alert engine\n"
        "    alerts/cause_engine.py         Hybrid cause diagnosis\n"
        "    api/server.py                 FastAPI inference service\n"
        "    dashboard/app.py              Streamlit 5-tab dashboard\n"
        "  models/                     Trained model artifacts\n"
        "  data/synthetic/             Generated temporal data\n"
        "  docs/                       Documentation + presentations"
    )
    pdf.multi_cell(0, 4.5, tree)

    # ═══════════════════════════════════════════════════
    # PAGE 10: Dashboard
    # ═══════════════════════════════════════════════════
    pdf.add_page()

    pdf.section_title("Interactive Dashboard", "9")

    pdf.body_text(
        "The Streamlit dashboard provides a 5-tab real-time monitoring interface with "
        "dark theme styling, designed for water utility control room operators:"
    )

    tabs = [
        ("Tab 1: Risk Overview",
         "Real-time WQRI timeline with color-coded zones, gauge visualization showing "
         "current risk level, per-sensor contribution breakdown bar chart, and multi-site "
         "comparison view. Live simulation mode auto-refreshes every 2 seconds."),
        ("Tab 2: Sensor Trends",
         "Individual sensor subplots with WHO/EPA regulatory thresholds overlaid as "
         "horizontal dashed lines. Interactive zoom, pan, and hover. Site + time range "
         "filtering in the sidebar."),
        ("Tab 3: Alerts Log",
         "Complete history of alert state transitions (normal -> warning -> critical) with "
         "timestamps, duration, and WQRI values. Color-coded severity. Summary statistics "
         "showing total alerts by type and average duration."),
        ("Tab 4: Root Cause Analysis",
         "Current diagnosis with confidence score, primary cause identification, ranked "
         "causes bar chart, event type distribution pie chart, and SHAP-based feature "
         "importance when available."),
        ("Tab 5: Data Table",
         "Raw sensor data table with conditional formatting (red for out-of-range values). "
         "CSV download button for offline analysis. Displays the most recent 500 readings "
         "for the selected site and time window."),
    ]
    for title, desc in tabs:
        pdf.sub_title(title)
        pdf.body_text(desc)

    # ═══════════════════════════════════════════════════
    # PAGE 11: Limitations & Future Work
    # ═══════════════════════════════════════════════════
    pdf.add_page()

    pdf.section_title("Limitations & Future Enhancements", "10")

    pdf.sub_title("Current Limitations")
    limitations = [
        "Synthetic data: temporal streams are generated from static CSV distributions, not real sensors.",
        "No true online learning: models are trained offline and served statically.",
        "Cause classifier imbalance: some rare events (stagnation) have limited training samples.",
        "Single-step forecasting: predicts only the next 5-min reading, not multi-horizon.",
        "No spatial modeling: sites are treated independently (no pipe network topology).",
        "No weather/demand data fusion: external factors not yet incorporated.",
    ]
    for l in limitations:
        pdf.bullet(l)

    pdf.ln(4)
    pdf.sub_title("Production Roadmap")
    phases = [
        "Phase 1: Real sensor integration via MQTT / OPC-UA / SCADA protocols",
        "Phase 2: Weather + water demand data fusion for improved forecasting",
        "Phase 3: LSTM / Temporal Fusion Transformer for multi-horizon prediction",
        "Phase 4: Graph Neural Networks incorporating pipe network topology",
        "Phase 5: Edge deployment using ONNX runtime on IoT gateway devices",
        "Phase 6: Docker + Kubernetes + Azure IoT Hub for scalable cloud deployment",
        "Phase 7: A/B testing framework for continuous model improvement",
        "Phase 8: Mobile alerts (SMS, push notifications) for field operators",
    ]
    for p in phases:
        pdf.bullet(p)

    pdf.ln(4)
    pdf.sub_title("Expected Production Performance Targets")
    pdf.metric_line("Potability AUC", "> 0.95", "(with real temporal data)")
    pdf.metric_line("Cause Classifier F1", "> 0.80", "(with balanced event data)")
    pdf.metric_line("False Alarm Rate", "< 5%", "(with tuned persistence)")
    pdf.metric_line("Detection Latency", "< 10 min", "(with 1-min sampling)")
    pdf.metric_line("Sites Supported", "100+", "(with horizontal scaling)")

    # ═══════════════════════════════════════════════════
    # PAGE 12: Conclusion
    # ═══════════════════════════════════════════════════
    pdf.add_page()

    pdf.section_title("Conclusion", "11")

    pdf.body_text(
        "AquaGuard demonstrates a complete, working AI pipeline for real-time urban "
        "drinking water quality monitoring. In just 10 hours, we built:\n\n"
        "  1. A synthetic data generator that creates realistic multi-site temporal streams\n"
        "  2. A 279-feature engineering pipeline capturing temporal dynamics\n"
        "  3. Three LightGBM model families (classification, multi-class, regression)\n"
        "  4. A composite WQRI score with false-alarm-resistant alert logic\n"
        "  5. A hybrid ML + rule-based cause identification engine\n"
        "  6. A FastAPI inference service with REST + WebSocket endpoints\n"
        "  7. A 5-tab Streamlit dashboard for real-time monitoring\n\n"
        "The system achieves 0.887 AUC for potability prediction, provides 15-40 minute "
        "early warning before unsafe conditions reach consumers, and automatically "
        "identifies the probable cause of degradation events.\n\n"
        "AquaGuard is designed for real-world impact: protecting public health through "
        "proactive, interpretable, AI-powered water quality monitoring."
    )

    pdf.ln(10)
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(*pdf.C_ACCENT)
    pdf.cell(0, 10, "AquaGuard -- Protecting Public Health with Real-Time AI",
             align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # Save
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    pdf.output(OUTPUT)
    print(f"PDF saved: {OUTPUT}")
    return OUTPUT


if __name__ == "__main__":
    build_pdf()
