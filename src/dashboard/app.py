"""
AquaGuard — Streamlit Dashboard
Real-time water quality monitoring, alerting, and root-cause analysis.

Run: streamlit run src/dashboard/app.py
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import time
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from config import (
    DATA_SYNTH, SENSOR_COLS, SITES, THRESHOLDS,
    RISK_WEIGHTS, CAUSE_CLASSES, ALERT_RISK_THRESHOLD, ALERT_CRITICAL_THRESHOLD,
)
from src.alerts.risk_index import (
    compute_risk_series, apply_alert_logic, get_risk_breakdown, compute_risk_index,
)
from src.alerts.cause_engine import rule_based_diagnosis, hybrid_diagnosis

# ── Page config ─────────────────────────────────────────
st.set_page_config(
    page_title="AquaGuard — Water Quality Monitor",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ──────────────────────────────────────────
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        color: white;
    }
    .risk-excellent { color: #00d26a; font-size: 2.5rem; font-weight: bold; }
    .risk-normal { color: #89cff0; font-size: 2.5rem; font-weight: bold; }
    .risk-caution { color: #ffc107; font-size: 2.5rem; font-weight: bold; }
    .risk-warning { color: #ff6b35; font-size: 2.5rem; font-weight: bold; }
    .risk-critical { color: #ff0054; font-size: 2.5rem; font-weight: bold; }
    .alert-banner-warning {
        background: #ff6b3520; border-left: 4px solid #ff6b35;
        padding: 0.8rem; margin: 0.5rem 0; border-radius: 4px;
    }
    .alert-banner-critical {
        background: #ff005420; border-left: 4px solid #ff0054;
        padding: 0.8rem; margin: 0.5rem 0; border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)


# ── Data loading ────────────────────────────────────────
@st.cache_data
def load_data():
    try:
        df = pd.read_parquet(DATA_SYNTH / "all_sites.parquet")
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df
    except FileNotFoundError:
        st.error("⚠️ Synthetic data not found. Run: `python src/data/synthetic_generator.py`")
        st.stop()


def get_risk_color(risk):
    if risk >= 80: return "#ff0054"
    elif risk >= 65: return "#ff6b35"
    elif risk >= 50: return "#ffc107"
    elif risk >= 30: return "#89cff0"
    else: return "#00d26a"


def get_risk_label(risk):
    if risk >= 80: return "CRITICAL"
    elif risk >= 65: return "WARNING"
    elif risk >= 50: return "CAUTION"
    elif risk >= 30: return "NORMAL"
    else: return "EXCELLENT"


# ── Sidebar ─────────────────────────────────────────────
st.sidebar.image("https://img.icons8.com/fluency/96/water.png", width=60)
st.sidebar.title("💧 AquaGuard")
st.sidebar.markdown("**Urban Water Quality Monitor**")
st.sidebar.markdown("---")

df = load_data()

# Site selector
selected_site = st.sidebar.selectbox("📍 Monitoring Site", SITES)

# Time range
time_options = {
    "Last 6 hours": 72,    # 72 readings × 5 min
    "Last 12 hours": 144,
    "Last 24 hours": 288,
    "Last 48 hours": 576,
    "Last 7 days": 2016,
    "All data": 0,
}
time_range = st.sidebar.selectbox("⏰ Time Range", list(time_options.keys()), index=2)
n_points = time_options[time_range]

# Filter data
site_df = df[df["site"] == selected_site].sort_values("timestamp").reset_index(drop=True)
if n_points > 0:
    site_df = site_df.tail(n_points).reset_index(drop=True)

# Compute risk
site_df["risk"] = compute_risk_series(site_df)
alerts = apply_alert_logic(site_df["risk"])
site_df["alert_level"] = alerts["alert_level"].values

# Live mode toggle
live_mode = st.sidebar.toggle("🔴 Live Simulation", value=False)

st.sidebar.markdown("---")
st.sidebar.markdown("**System Status**")
n_warnings = (site_df["alert_level"] == "warning").sum()
n_critical = (site_df["alert_level"] == "critical").sum()
st.sidebar.metric("Warnings", n_warnings)
st.sidebar.metric("Critical Alerts", n_critical)

# ── Main content ────────────────────────────────────────
# Header
col_title, col_status = st.columns([3, 1])
with col_title:
    st.title("💧 AquaGuard — Real-Time Water Quality Monitor")
    st.caption(f"Site: **{selected_site}** | Range: {time_range} | {len(site_df):,} readings")

with col_status:
    current_risk = site_df["risk"].iloc[-1] if len(site_df) > 0 else 0
    label = get_risk_label(current_risk)
    color = get_risk_color(current_risk)
    st.markdown(f"""
    <div class="metric-card">
        <div style="font-size: 0.9rem; opacity: 0.7;">Current Risk Index</div>
        <div style="color: {color}; font-size: 2.8rem; font-weight: bold;">{current_risk:.0f}</div>
        <div style="color: {color}; font-size: 1.1rem;">{label}</div>
    </div>
    """, unsafe_allow_html=True)

# ── Alert Banner ────────────────────────────────────────
current_alert = site_df["alert_level"].iloc[-1] if len(site_df) > 0 else "normal"
if current_alert == "critical":
    # Get cause
    latest = site_df.iloc[-1]
    cause = hybrid_diagnosis(latest.to_dict())
    st.markdown(f"""
    <div class="alert-banner-critical">
        🚨 <b>CRITICAL ALERT</b> — Risk Index: {current_risk:.0f}/100<br>
        Probable cause: <b>{cause['primary_cause'].replace('_', ' ').title()}</b>
        (confidence: {cause['confidence']:.0%})<br>
        {cause.get('rule_explanations', [''])[0] if cause.get('rule_explanations') else ''}
    </div>
    """, unsafe_allow_html=True)
elif current_alert == "warning":
    latest = site_df.iloc[-1]
    cause = hybrid_diagnosis(latest.to_dict())
    st.markdown(f"""
    <div class="alert-banner-warning">
        ⚠️ <b>WARNING</b> — Risk Index: {current_risk:.0f}/100<br>
        Probable cause: <b>{cause['primary_cause'].replace('_', ' ').title()}</b>
        (confidence: {cause['confidence']:.0%})
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ═══════════════════════════════════════════════════════
# TAB LAYOUT
# ═══════════════════════════════════════════════════════
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Risk Overview", "📈 Sensor Trends", "🚨 Alerts Log",
    "🔍 Root Cause Analysis", "📋 Data Table"
])

# ── TAB 1: Risk Overview ───────────────────────────────
with tab1:
    col1, col2 = st.columns([2, 1])

    with col1:
        # Risk timeline
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=site_df["timestamp"], y=site_df["risk"],
            mode="lines", name="Risk Index",
            line=dict(color="#4ecdc4", width=2),
            fill="tozeroy",
            fillcolor="rgba(78, 205, 196, 0.1)",
        ))
        # Threshold lines
        fig.add_hline(y=65, line_dash="dash", line_color="#ff6b35",
                      annotation_text="Warning (65)")
        fig.add_hline(y=80, line_dash="dash", line_color="#ff0054",
                      annotation_text="Critical (80)")

        # Color-code event regions
        events = site_df[site_df["event_type"] != "normal"]
        if not events.empty:
            for etype in events["event_type"].unique():
                evt_data = events[events["event_type"] == etype]
                fig.add_trace(go.Scatter(
                    x=evt_data["timestamp"], y=evt_data["risk"],
                    mode="markers", name=etype.replace("_", " ").title(),
                    marker=dict(size=4, opacity=0.6),
                ))

        fig.update_layout(
            title="Water Quality Risk Index Over Time",
            yaxis_title="Risk Score (0-100)",
            yaxis_range=[0, 105],
            template="plotly_dark",
            height=400,
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Risk gauge
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=current_risk,
            title={"text": "Current WQRI"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": get_risk_color(current_risk)},
                "steps": [
                    {"range": [0, 30], "color": "rgba(0,210,106,0.13)"},
                    {"range": [30, 50], "color": "rgba(137,207,240,0.13)"},
                    {"range": [50, 65], "color": "rgba(255,193,7,0.13)"},
                    {"range": [65, 80], "color": "rgba(255,107,53,0.13)"},
                    {"range": [80, 100], "color": "rgba(255,0,84,0.13)"},
                ],
                "threshold": {
                    "line": {"color": "white", "width": 4},
                    "thickness": 0.75,
                    "value": current_risk,
                },
            },
        ))
        fig_gauge.update_layout(height=250, template="plotly_dark")
        st.plotly_chart(fig_gauge, use_container_width=True)

        # Per-sensor contribution
        st.subheader("Sensor Risk Contributions")
        if len(site_df) > 0:
            latest = site_df.iloc[-1]
            breakdown = get_risk_breakdown(latest)
            contrib_df = pd.DataFrame([
                {"Sensor": k, "Contribution": v["contribution"],
                 "Value": f"{v['value']:.2f} {v['unit']}",
                 "Safe Range": v["safe_range"]}
                for k, v in breakdown.items()
            ]).sort_values("Contribution", ascending=False)

            fig_bar = px.bar(
                contrib_df, x="Contribution", y="Sensor",
                orientation="h", color="Contribution",
                color_continuous_scale="RdYlGn_r",
                text="Value",
            )
            fig_bar.update_layout(
                height=300, template="plotly_dark",
                showlegend=False, yaxis=dict(autorange="reversed"),
            )
            st.plotly_chart(fig_bar, use_container_width=True)

    # Multi-site comparison
    st.subheader("🏭 Multi-Site Risk Comparison")
    site_latest = []
    for site in SITES:
        sdf = df[df["site"] == site].sort_values("timestamp")
        if len(sdf) > 0:
            risk = compute_risk_series(sdf.tail(50))
            site_latest.append({
                "Site": site,
                "Current Risk": round(risk.iloc[-1], 1),
                "Avg Risk (24h)": round(risk.mean(), 1),
                "Max Risk (24h)": round(risk.max(), 1),
                "Status": get_risk_label(risk.iloc[-1]),
            })
    compare_df = pd.DataFrame(site_latest)
    st.dataframe(compare_df, use_container_width=True, hide_index=True)


# ── TAB 2: Sensor Trends ──────────────────────────────
with tab2:
    st.subheader("📈 Sensor Trends vs. Regulatory Limits")

    selected_sensors = st.multiselect(
        "Select sensors to display",
        SENSOR_COLS,
        default=["chloramine", "turbidity", "ph", "conductivity"],
    )

    if selected_sensors:
        n_sensors = len(selected_sensors)
        fig = make_subplots(
            rows=n_sensors, cols=1, shared_xaxes=True,
            subplot_titles=[s.replace("_", " ").title() for s in selected_sensors],
            vertical_spacing=0.04,
        )

        for i, sensor in enumerate(selected_sensors, 1):
            if sensor in site_df.columns:
                fig.add_trace(go.Scatter(
                    x=site_df["timestamp"], y=site_df[sensor],
                    mode="lines", name=sensor,
                    line=dict(width=1.5),
                ), row=i, col=1)

                # Add threshold bands
                if sensor in THRESHOLDS:
                    th = THRESHOLDS[sensor]
                    if th["high"] < site_df[sensor].max() * 3:
                        fig.add_hline(
                            y=th["high"], line_dash="dot",
                            line_color="red", row=i, col=1,
                            annotation_text=f"Max: {th['high']} {th['unit']}",
                        )
                    if th["low"] > 0:
                        fig.add_hline(
                            y=th["low"], line_dash="dot",
                            line_color="orange", row=i, col=1,
                            annotation_text=f"Min: {th['low']} {th['unit']}",
                        )

        fig.update_layout(
            height=250 * n_sensors,
            template="plotly_dark",
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)


# ── TAB 3: Alerts Log ─────────────────────────────────
with tab3:
    st.subheader("🚨 Alert History")

    # Alert transitions
    alert_changes = site_df[site_df["alert_level"].shift() != site_df["alert_level"]].copy()
    if len(alert_changes) > 0:
        alert_log = alert_changes[["timestamp", "alert_level", "risk", "event_type"]].copy()
        alert_log.columns = ["Time", "Alert Level", "Risk Score", "Event Type"]
        alert_log = alert_log.sort_values("Time", ascending=False)

        # Color code
        def color_alert(val):
            if val == "critical":
                return "background-color: #ff005430; color: #ff0054"
            elif val == "warning":
                return "background-color: #ff6b3530; color: #ff6b35"
            return ""

        st.dataframe(
            alert_log.style.map(color_alert, subset=["Alert Level"]),
            use_container_width=True,
            hide_index=True,
            height=400,
        )

        # Alert statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Alerts", len(alert_log[alert_log["Alert Level"] != "normal"]))
        with col2:
            st.metric("Critical Events", len(alert_log[alert_log["Alert Level"] == "critical"]))
        with col3:
            st.metric("Warnings", len(alert_log[alert_log["Alert Level"] == "warning"]))
        with col4:
            # False alarm estimate: alerts on "normal" event_type
            false_alarms = alert_log[
                (alert_log["Alert Level"] != "normal") &
                (alert_log["Event Type"] == "normal")
            ]
            st.metric("Est. False Alarms", len(false_alarms))
    else:
        st.info("No alert transitions in the selected time range.")


# ── TAB 4: Root Cause Analysis ─────────────────────────
with tab4:
    st.subheader("🔍 Root Cause Analysis — Latest Reading")

    if len(site_df) > 0:
        latest = site_df.iloc[-1]
        diagnosis = hybrid_diagnosis(latest.to_dict())

        col1, col2 = st.columns([1, 1])

        with col1:
            st.markdown("### Primary Diagnosis")
            cause = diagnosis["primary_cause"]
            conf = diagnosis["confidence"]

            cause_descriptions = {
                "normal": "✅ All parameters within expected ranges",
                "disinfectant_decay": "🧪 Disinfectant (chloramine) levels declining — pathogen risk",
                "contamination_intrusion": "🚱 External contamination detected — possible pipe break",
                "pipe_corrosion": "🔧 Pipe corrosion indicators — metal leaching",
                "stagnation": "💤 Water stagnation in distribution network",
                "operational_change": "⚙️ Treatment or operational parameter change detected",
                "sensor_fault": "📡 Sensor malfunction — readings unreliable",
            }

            emoji_cause = cause_descriptions.get(cause, cause)
            st.markdown(f"**{emoji_cause}**")
            st.progress(conf, text=f"Confidence: {conf:.0%}")

            # Rule explanations
            if diagnosis.get("rule_explanations"):
                st.markdown("**Rule-based evidence:**")
                for expl in diagnosis["rule_explanations"]:
                    st.markdown(f"- {expl}")

        with col2:
            st.markdown("### All Possible Causes")
            if diagnosis.get("all_causes"):
                cause_df = pd.DataFrame(diagnosis["all_causes"])
                fig = px.bar(
                    cause_df, x="score", y="cause", orientation="h",
                    color="score", color_continuous_scale="Reds",
                    labels={"cause": "Cause", "score": "Score"},
                )
                fig.update_layout(
                    height=250, template="plotly_dark", showlegend=False,
                    yaxis=dict(autorange="reversed"),
                )
                st.plotly_chart(fig, use_container_width=True)

        # Event timeline in data
        st.markdown("### 📅 Event History")
        event_counts = site_df[site_df["event_type"] != "normal"]["event_type"].value_counts()
        if len(event_counts) > 0:
            fig_pie = px.pie(
                values=event_counts.values,
                names=event_counts.index,
                title="Event Type Distribution",
                color_discrete_sequence=px.colors.qualitative.Set2,
            )
            fig_pie.update_layout(height=300, template="plotly_dark")
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.success("No degradation events detected in this time range.")


# ── TAB 5: Data Table ──────────────────────────────────
with tab5:
    st.subheader("📋 Raw Sensor Data")
    display_cols = ["timestamp", "site"] + SENSOR_COLS + ["risk", "alert_level", "event_type"]
    available_cols = [c for c in display_cols if c in site_df.columns]
    st.dataframe(
        site_df[available_cols].tail(200).sort_values("timestamp", ascending=False),
        use_container_width=True,
        hide_index=True,
        height=500,
    )

    # Download button
    csv = site_df[available_cols].to_csv(index=False)
    st.download_button("📥 Download Data (CSV)", csv, "aquaguard_data.csv", "text/csv")

# ── Live simulation ────────────────────────────────────
if live_mode:
    st.markdown("---")
    st.subheader("🔴 Live Simulation Feed")
    placeholder = st.empty()
    chart_placeholder = st.empty()

    # Simulate streaming through data
    for i in range(min(100, len(site_df))):
        row = site_df.iloc[i]
        risk = row["risk"]
        color = get_risk_color(risk)
        label = get_risk_label(risk)

        with placeholder.container():
            cols = st.columns(len(SENSOR_COLS) + 1)
            cols[0].metric("Risk", f"{risk:.0f}", label)
            for j, sensor in enumerate(SENSOR_COLS):
                if sensor in row.index and not pd.isna(row[sensor]):
                    cols[j + 1].metric(
                        sensor.replace("_", " ").title()[:10],
                        f"{row[sensor]:.1f}",
                    )

        time.sleep(0.5)

# Footer
st.markdown("---")
st.caption("AquaGuard v1.0 | AI Night Challenge 2026 | Real-time Urban Water Quality Monitoring")
