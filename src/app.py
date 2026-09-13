import sys
from pathlib import Path

# Add src and project root to sys.path
SRC_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SRC_DIR.parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# Backend imports
from backend.data.loader import PortDataLoader
from backend.data.generator import PortDataGenerator
from backend.models.features import PortFeatureEngineer
from backend.models.congestion_model import CongestionRiskPredictor
from backend.models.hotspot_detector import HotspotDetector
from backend.optimization.routing import AlternateRoutingEngine
from backend.optimization.berth_optimizer import BerthOptimizer
from backend.optimization.crane_optimizer import CraneOptimizer
from backend.planner.plan_generator import OperationalPlanGenerator
from backend.planner.metrics import PortMetricsCalculator
from backend.copilot.explainability import ExplainabilityEngine
from backend.copilot.scenario_simulator import ScenarioSimulator
from backend.copilot.bob_agent import BobCopilotAgent

st.set_page_config(
    page_title="Port Operations Copilot | IBM Bob Hackathon",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #0F62FE;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #525252;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #f4f7fb;
        border-left: 5px solid #0F62FE;
        padding: 15px;
        border-radius: 6px;
        margin-bottom: 10px;
    }
    .alert-card-critical {
        background-color: #FFF1F1;
        border-left: 5px solid #DA1E28;
        padding: 14px;
        border-radius: 6px;
        margin-bottom: 12px;
    }
    .alert-card-warning {
        background-color: #FDF8E2;
        border-left: 5px solid #F1C21B;
        padding: 14px;
        border-radius: 6px;
        margin-bottom: 12px;
    }
    .alert-card-success {
        background-color: #DEFBE6;
        border-left: 5px solid #24A148;
        padding: 14px;
        border-radius: 6px;
        margin-bottom: 12px;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def load_base_data_and_models():
    loader = PortDataLoader()
    try:
        data = loader.load_all_data()
    except Exception:
        gen = PortDataGenerator()
        sample_dir = Path(__file__).resolve().parent / "backend" / "data" / "sample_data"
        data = gen.generate_all(sample_dir)
        
    feature_eng = PortFeatureEngineer()
    predictor = CongestionRiskPredictor()
    detector = HotspotDetector()
    routing_engine = AlternateRoutingEngine()
    berth_opt = BerthOptimizer(time_limit_seconds=20)
    crane_opt = CraneOptimizer()
    plan_gen = OperationalPlanGenerator()
    metrics_calc = PortMetricsCalculator()
    explain_engine = ExplainabilityEngine()
    simulator = ScenarioSimulator()
    bob_agent = BobCopilotAgent()

    return {
        "data": data,
        "feature_eng": feature_eng,
        "predictor": predictor,
        "detector": detector,
        "routing_engine": routing_engine,
        "berth_opt": berth_opt,
        "crane_opt": crane_opt,
        "plan_gen": plan_gen,
        "metrics_calc": metrics_calc,
        "explain_engine": explain_engine,
        "simulator": simulator,
        "bob_agent": bob_agent
    }

pipeline = load_base_data_and_models()

# Compute live baseline state
vessels_df = pipeline["data"]["vessels"].copy()
berths_df = pipeline["data"]["berths"].copy()
cranes_df = pipeline["data"]["cranes"].copy()
terminals_df = pipeline["data"]["terminals"].copy()

# Feature extraction & ML risk scoring
features_df = pipeline["feature_eng"].extract_terminal_hourly_features(vessels_df, berths_df, cranes_df, terminals_df)
scored_features_df = pipeline["predictor"].predict_features_dataframe(features_df)
hotspots = pipeline["detector"].detect_hotspots(scored_features_df, vessels_df, terminals_df)

# Rerouting & Optimization
routing_recs = pipeline["routing_engine"].evaluate_routing_recommendations(
    vessels_df, terminals_df, berths_df, hotspots, scored_features_df
)
reroute_overrides = {r["vessel_id"]: r["recommended_terminal"] for r in routing_recs}
berth_res = pipeline["berth_opt"].optimize_berth_allocations(vessels_df, berths_df, rerouting_overrides=reroute_overrides)
crane_sched_df = pipeline["crane_opt"].optimize_crane_assignments(berth_res["schedule"], cranes_df)
plan_df = pipeline["plan_gen"].generate_72h_plan(crane_sched_df, routing_recs, scored_features_df)
baseline_df = pipeline["metrics_calc"].compute_baseline_plan(vessels_df, berths_df)
kpis = pipeline["metrics_calc"].calculate_comparative_kpis(baseline_df, plan_df, berths_df)

# Sidebar
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/5/51/IBM_logo.svg", width=110)
st.sidebar.markdown("### **Port Operations Copilot**")
st.sidebar.caption("IBM Bob AI Hackathon — Official Submission")

selected_tab = st.sidebar.radio(
    "Operational Modules",
    [
        "📊 Port Executive Overview",
        "🚨 Congestion & Hotspots",
        "⚡ Berth & Crane Optimization",
        "📋 72-Hour Operations Plan",
        "💡 Recommendations & Explainability",
        "🧪 Scenario & What-If Studio",
        "🤖 IBM Bob Copilot (AI Q&A)"
    ]
)

st.sidebar.markdown("---")
st.sidebar.markdown("**Port Complex**: San Pedro Bay Complex")
st.sidebar.markdown(f"**Vessels in Scope**: {len(vessels_df)} calls")
st.sidebar.markdown(f"**Planning Horizon**: 72 Hours")
st.sidebar.markdown(f"**Active Berths**: {len(berths_df[berths_df['status']=='ACTIVE'])}")
st.sidebar.markdown(f"**Operational Cranes**: {len(cranes_df[cranes_df['status']=='OPERATIONAL'])}")

# -------------------------------------------------------------
# TAB 1: EXECUTIVE OVERVIEW
# -------------------------------------------------------------
if selected_tab == "📊 Port Executive Overview":
    st.markdown('<div class="main-header">🚢 Port Operations Executive Overview</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Real-time terminal congestion monitoring, prescriptive AI recommendations, and rolling 72-hour operational metrics.</div>', unsafe_allow_html=True)

    # Top Alert Banner if Hotspot exists
    if hotspots:
        top_spot = hotspots[0]
        st.markdown(f"""
        <div class="alert-card-critical">
            <strong>⚠️ CRITICAL BOTTLENECK PREDICTED:</strong> Terminal {top_spot['terminal_id']} is projected to reach 
            <strong>{top_spot['peak_risk_score']}/100 Risk</strong> between <strong>Hours {int(top_spot['start_hour'])} and {int(top_spot['end_hour'])}</strong> 
            impacting {top_spot['affected_count']} container vessels ({top_spot['total_teu_at_risk']:,} TEU). 
            <em>Optimizer recommends proactive alternate routing for {len(routing_recs)} vessel(s).</em>
        </div>
        """, unsafe_allow_html=True)

    # KPI Top Metric Row
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Vessels", f"{len(vessels_df)}", "72h Window")
    c2.metric("Avg Wait Time", f"{kpis['optimized']['avg_waiting_time_hours']} hrs", f"-{kpis['improvements']['avg_waiting_time_reduction_pct']}% vs Base")
    c3.metric("Max Wait Time", f"{kpis['optimized']['max_waiting_time_hours']} hrs", f"-{kpis['improvements']['max_waiting_time_reduction_pct']}% vs Base")
    c4.metric("Dwell Saved", f"{kpis['improvements']['total_vessel_hours_saved']} hrs", "Fleet Productivity")
    c5.metric("Hotspots Mitigated", f"{len(hotspots)} Active", f"{kpis['optimized']['rerouted_vessels_count']} Rerouted")

    st.markdown("---")

    # Layout: Gauges and Terminal Capacity Overview
    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("📈 Terminal Utilization & Yard Pressure")
        term_summary = []
        for _, t in terminals_df.iterrows():
            t_id = t["terminal_id"]
            t_hotspots = [h for h in hotspots if h["terminal_id"] == t_id]
            max_risk = max([h["peak_risk_score"] for h in t_hotspots]) if t_hotspots else 28.0
            term_summary.append({
                "Terminal": f"{t['terminal_name']} ({t_id})",
                "Yard Capacity (TEU)": f"{t['yard_capacity']:,}",
                "Yard Utilization": f"{int(t['current_yard_utilization']*100)}%",
                "Peak Risk": f"{max_risk}/100",
                "Status": "CRITICAL RISK" if max_risk >= 75 else ("ELEVATED" if max_risk >= 50 else "OPTIMAL")
            })
        st.dataframe(pd.DataFrame(term_summary), width='stretch', hide_index=True)

        # Baseline vs Optimized Comparison Bar Chart
        kpi_compare = pd.DataFrame({
            "Metric": ["Avg Waiting Time (hrs)", "Max Waiting Time (hrs)", "Delayed Vessels (>3h)"],
            "Unoptimized Baseline (FIFO)": [kpis["baseline"]["avg_waiting_time_hours"], kpis["baseline"]["max_waiting_time_hours"], kpis["baseline"]["delayed_vessels_count"]],
            "AI & OR-Tools Optimized": [kpis["optimized"]["avg_waiting_time_hours"], kpis["optimized"]["max_waiting_time_hours"], kpis["optimized"]["delayed_vessels_count"]]
        })
        fig_comp = px.bar(
            kpi_compare, x="Metric", y=["Unoptimized Baseline (FIFO)", "AI & OR-Tools Optimized"],
            barmode="group", color_discrete_sequence=["#FA4D56", "#0F62FE"],
            title="Operational Impact: Baseline vs. Optimized Plan"
        )
        fig_comp.update_layout(height=320, margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig_comp, width='stretch')

    with col_right:
        st.subheader("⏱️ 72-Hour Congestion Heatmap")
        pivot_risk = scored_features_df.pivot(index="terminal_id", columns="hour", values="risk_score")
        fig_heat = px.imshow(
            pivot_risk,
            labels=dict(x="Planning Hour (0 - 72)", y="Terminal", color="Risk Score"),
            x=[f"H{int(c)}" for c in pivot_risk.columns],
            y=pivot_risk.index,
            color_continuous_scale="RdYlGn_r",
            zmin=0, zmax=100,
            title="Hourly Terminal Congestion Risk Index"
        )
        fig_heat.update_layout(height=320, margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig_heat, width='stretch')

        st.info("💡 **Key Insight**: Terminal T2 experiences an intense arrival surge between Hours 14-30. Proactive rerouting to Terminal T3 prevents severe multi-day queuing.")

# -------------------------------------------------------------
# TAB 2: CONGESTION & HOTSPOTS
# -------------------------------------------------------------
elif selected_tab == "🚨 Congestion & Hotspots":
    st.markdown('<div class="main-header">🚨 Congestion Hotspots & Predictive Risk</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Temporal sliding window analysis, demand-to-capacity metrics, and automated bottleneck detection.</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📊 Hourly Terminal Risk Curves")
        fig_lines = px.line(
            scored_features_df, x="hour", y="risk_score", color="terminal_id",
            labels={"hour": "Planning Horizon (Hours)", "risk_score": "Congestion Risk Score (0-100)", "terminal_id": "Terminal"},
            color_discrete_map={"T1": "#0F62FE", "T2": "#DA1E28", "T3": "#24A148"},
            title="Predicted Congestion Trajectory by Terminal"
        )
        fig_lines.add_hline(y=75, line_dash="dash", line_color="red", annotation_text="CRITICAL (75+)")
        fig_lines.add_hline(y=50, line_dash="dash", line_color="orange", annotation_text="HIGH RISK (50+)")
        fig_lines.update_layout(height=360, margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig_lines, width='stretch')

    with col2:
        st.subheader("🎯 Hotspot Diagnostics")
        for spot in hotspots:
            st.markdown(f"""
            <div class="{'alert-card-critical' if spot['severity']=='CRITICAL' else 'alert-card-warning'}">
                <strong>{spot['hotspot_id']} — {spot['severity']}</strong><br/>
                <strong>Window:</strong> Hours {int(spot['start_hour'])} - {int(spot['end_hour'])} ({spot['duration_hours']} hrs)<br/>
                <strong>Peak Risk:</strong> {spot['peak_risk_score']}/100<br/>
                <strong>Root Cause:</strong> {spot['primary_root_cause']}<br/>
                <strong>Vessels at Risk:</strong> {spot['affected_count']} ({spot['total_teu_at_risk']:,} TEU)
            </div>
            """, unsafe_allow_html=True)

    st.subheader("📈 Demand vs Capacity Factors")
    c_a, c_b = st.columns(2)
    with c_a:
        fig_berth_p = px.line(
            scored_features_df, x="hour", y="berth_pressure_ratio", color="terminal_id",
            labels={"berth_pressure_ratio": "Berth Demand / Capacity Ratio", "hour": "Hour"},
            title="Berth Occupancy Demand Pressure (Ratio > 1.0 = Queuing)"
        )
        fig_berth_p.add_hline(y=1.0, line_dash="dash", line_color="gray")
        fig_berth_p.update_layout(height=280)
        st.plotly_chart(fig_berth_p, width='stretch')
    with c_b:
        fig_crane_p = px.line(
            scored_features_df, x="hour", y="crane_pressure_ratio", color="terminal_id",
            labels={"crane_pressure_ratio": "Crane Workload Pressure Ratio", "hour": "Hour"},
            title="Crane Discharge Rate vs Supply"
        )
        fig_crane_p.add_hline(y=1.0, line_dash="dash", line_color="gray")
        fig_crane_p.update_layout(height=280)
        st.plotly_chart(fig_crane_p, width='stretch')

# -------------------------------------------------------------
# TAB 3: BERTH & CRANE OPTIMIZATION
# -------------------------------------------------------------
elif selected_tab == "⚡ Berth & Crane Optimization":
    st.markdown('<div class="main-header">⚡ Google OR-Tools Berth & Crane Allocation</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Mixed Integer Constraint Programming (CP-SAT) schedules non-overlapping berth intervals and dynamic crane gangs.</div>', unsafe_allow_html=True)

    # Gantt Chart of Berth Schedule
    gantt_df = plan_df.copy()
    gantt_df["Start_Date"] = pd.to_datetime("2026-09-15 00:00") + pd.to_timedelta(gantt_df["start_time_hour"], unit="h")
    gantt_df["End_Date"] = pd.to_datetime("2026-09-15 00:00") + pd.to_timedelta(gantt_df["end_time_hour"], unit="h")

    fig_gantt = px.timeline(
        gantt_df, x_start="Start_Date", x_end="End_Date", y="assigned_berth", color="priority",
        hover_data=["vessel_id", "vessel_name", "containers", "cranes_assigned", "waiting_time_hours", "routing_status"],
        category_orders={"assigned_berth": sorted(berths_df["berth_id"].unique()), "priority": ["CRITICAL", "HIGH", "NORMAL", "LOW"]},
        color_discrete_map={"CRITICAL": "#DA1E28", "HIGH": "#FF832B", "NORMAL": "#0F62FE", "LOW": "#8A3FFC"},
        title="72-Hour Optimized Berth Allocation Schedule (Gantt)"
    )
    fig_gantt.update_yaxes(autorange="reversed")
    fig_gantt.update_layout(height=420, margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig_gantt, width='stretch')

    c1, c2 = st.columns([1, 1])
    with c1:
        st.subheader("🏗️ Dynamic Crane Gang Allocation")
        fig_crane_hist = px.histogram(
            plan_df, x="cranes_assigned", color="priority",
            labels={"cranes_assigned": "Number of STS Cranes Assigned", "count": "Vessel Calls"},
            barmode="group",
            title="Crane Assignment Distribution by Vessel Priority"
        )
        fig_crane_hist.update_layout(height=300)
        st.plotly_chart(fig_crane_hist, width='stretch')

    with c2:
        st.subheader("⏱️ Vessel Waiting Time Distribution")
        fig_wait = px.histogram(
            plan_df, x="waiting_time_hours", nbins=15, color_discrete_sequence=["#0F62FE"],
            labels={"waiting_time_hours": "Waiting Time at Anchor (Hours)"},
            title="Optimized Wait Time Histogram (Avg: " + str(kpis['optimized']['avg_waiting_time_hours']) + " hrs)"
        )
        fig_wait.update_layout(height=300)
        st.plotly_chart(fig_wait, width='stretch')

# -------------------------------------------------------------
# TAB 4: 72-HOUR OPERATIONS PLAN
# -------------------------------------------------------------
elif selected_tab == "📋 72-Hour Operations Plan":
    st.markdown('<div class="main-header">📋 72-Hour Rolling Master Operations Plan</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Interactive master schedule for shift supervisors, harbor pilots, and stevedoring managers.</div>', unsafe_allow_html=True)

    # Filters
    f1, f2, f3 = st.columns(3)
    with f1:
        sel_term = st.multiselect("Filter by Terminal", options=terminals_df["terminal_id"].unique(), default=terminals_df["terminal_id"].unique())
    with f2:
        sel_prio = st.multiselect("Filter by Priority", options=["CRITICAL", "HIGH", "NORMAL", "LOW"], default=["CRITICAL", "HIGH", "NORMAL", "LOW"])
    with f3:
        search_v = st.text_input("Search Vessel Name or ID", "")

    filtered_plan = plan_df[
        (plan_df["assigned_terminal"].isin(sel_term)) &
        (plan_df["priority"].isin(sel_prio))
    ]
    if search_v:
        filtered_plan = filtered_plan[
            filtered_plan["vessel_name"].str.contains(search_v, case=False) |
            filtered_plan["vessel_id"].str.contains(search_v, case=False)
        ]

    st.dataframe(
        filtered_plan[[
            "vessel_id", "vessel_name", "priority", "vessel_size", "containers",
            "eta_hour", "assigned_terminal", "assigned_berth", "start_time_hour", "end_time_hour",
            "waiting_time_hours", "cranes_assigned", "routing_status", "action_required"
        ]],
        width='stretch',
        hide_index=True
    )

    csv_data = filtered_plan.to_csv(index=False).encode('utf-8')
    st.download_button(
        "📥 Download 72-Hour Operational Plan (CSV)",
        data=csv_data,
        file_name="port_operations_72h_plan.csv",
        mime="text/csv"
    )

# -------------------------------------------------------------
# TAB 5: RECOMMENDATIONS & EXPLAINABILITY
# -------------------------------------------------------------
elif selected_tab == "💡 Recommendations & Explainability":
    st.markdown('<div class="main-header">💡 Prescriptive Recommendations & Transparent AI Audit</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Auditable rationale behind every rerouting decision, berth assignment, and crane allocation.</div>', unsafe_allow_html=True)

    st.subheader("🔀 Proactive Alternate Terminal Rerouting Recommendations")
    if routing_recs:
        for rec in routing_recs:
            st.markdown(f"""
            <div class="alert-card-success">
                <h4>🚢 {rec['vessel_name']} ({rec['vessel_id']}) — Reroute Recommended</h4>
                <strong>Action:</strong> Divert from <strong>{rec['original_terminal_name']} ({rec['original_terminal']})</strong> 
                → <strong>{rec['recommended_terminal_name']} ({rec['recommended_terminal']})</strong><br/>
                <strong>Turnaround Savings:</strong> ⏱️ <strong>{rec['estimated_time_savings_hrs']} hours saved</strong> 
                (Expected wait drops from {rec['estimated_wait_time_original_hrs']}h to {rec['estimated_wait_time_rerouted_hrs']}h)<br/>
                <strong>Cargo Impact:</strong> {rec['teu_volume']:,} TEU load balanced<br/>
                <strong>Justification:</strong> {rec['reasoning']}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.success("No vessel rerouting required. All vessels operate within standard capacity.")

    st.markdown("---")
    st.subheader("🔍 Individual Vessel Decision Audit Card (6-Point Explainability)")
    
    sel_vessel_id = st.selectbox("Select Vessel to Inspect Audit Trail:", options=plan_df["vessel_id"].tolist())
    audit_card = pipeline["explain_engine"].generate_vessel_audit_card(
        sel_vessel_id, plan_df, routing_recs, hotspots, terminals_df
    )

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(f"**1. What Happened?**\n\n{audit_card['what_happened']}")
        st.markdown(f"**2. Why Is This a Problem?**\n\n{audit_card['why_is_this_a_problem']}")
        st.markdown(f"**3. What Does the System Predict?**\n\n{audit_card['what_system_predicts']}")
    with col_b:
        st.markdown(f"**4. What Action Is Recommended?**\n\n{audit_card['recommended_action']}")
        st.markdown(f"**5. Why Was This Action Selected?**\n\n{audit_card['why_action_selected']}")
        st.markdown(f"**6. What Constraints Influenced the Decision?**\n\n{audit_card['constraints_considered']}")

# -------------------------------------------------------------
# TAB 6: SCENARIO & WHAT-IF STUDIO
# -------------------------------------------------------------
elif selected_tab == "🧪 Scenario & What-If Studio":
    st.markdown('<div class="main-header">🧪 Scenario & What-If Disruption Studio</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Perturb vessel schedules, simulate crane breakdowns or weather delays, and recalculate the OR-Tools master schedule live.</div>', unsafe_allow_html=True)

    with st.expander("⚙️ Configure Disruption Scenario", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            sim_vessel = st.selectbox("Select Vessel to Delay", options=["None"] + vessels_df["vessel_id"].tolist(), index=1)
            sim_delay_hours = st.slider("Arrival Delay (Hours)", min_value=0.0, max_value=18.0, value=6.0, step=1.0)
        with c2:
            sim_crane_outage = st.multiselect("Simulate Crane Outages", options=cranes_df["crane_id"].tolist(), default=["CR-102"])
        with c3:
            sim_surge_pct = st.slider("Cargo Volume Surge (+%)", min_value=0, max_value=50, value=0, step=5)

    if st.button("🚀 Run Live Scenario Optimization", type="primary"):
        with st.spinner("Re-executing Google OR-Tools CP-SAT and predictive models..."):
            v_id_param = None if sim_vessel == "None" else sim_vessel
            sim_res = pipeline["simulator"].run_simulation(
                base_vessels_df=vessels_df,
                base_berths_df=berths_df,
                base_cranes_df=cranes_df,
                base_terminals_df=terminals_df,
                delayed_vessel_id=v_id_param,
                delay_hours=sim_delay_hours,
                offline_crane_ids=sim_crane_outage,
                cargo_surge_pct=float(sim_surge_pct)
            )
            sim_kpis = sim_res["kpi_metrics"]

            st.success("✅ Scenario recalculated successfully in real-time!")

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Scenario Avg Wait", f"{sim_kpis['optimized']['avg_waiting_time_hours']} hrs", f"Delta: {round(sim_kpis['optimized']['avg_waiting_time_hours'] - kpis['optimized']['avg_waiting_time_hours'], 2)}h")
            m2.metric("Scenario Max Wait", f"{sim_kpis['optimized']['max_waiting_time_hours']} hrs", f"Delta: {round(sim_kpis['optimized']['max_waiting_time_hours'] - kpis['optimized']['max_waiting_time_hours'], 2)}h")
            m3.metric("Rerouted Vessels", f"{sim_kpis['optimized']['rerouted_vessels_count']}", f"vs Base Plan: {kpis['optimized']['rerouted_vessels_count']}")
            m4.metric("Dwell Hours Saved", f"{sim_kpis['improvements']['total_vessel_hours_saved']} hrs", "vs Naive FIFO")

            st.subheader("📊 Recalculated Master Plan (First 10 Vessels)")
            st.dataframe(
                sim_res["plan_df"][[
                    "vessel_id", "vessel_name", "eta_hour", "assigned_berth", "start_time_hour",
                    "end_time_hour", "waiting_time_hours", "cranes_assigned", "routing_status"
                ]].head(10),
                width='stretch',
                hide_index=True
            )

# -------------------------------------------------------------
# TAB 7: IBM BOB COPILOT
# -------------------------------------------------------------
elif selected_tab == "🤖 IBM Bob Copilot (AI Q&A)":
    st.markdown('<div class="main-header">🤖 IBM Bob Port Operations Copilot</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Ask operational questions in natural language grounded directly in live port telemetry, OR-Tools schedules, and ML models.</div>', unsafe_allow_html=True)

    # Preset Quick Buttons from Challenge Spec
    st.markdown("**⚡ Quick Operational Questions (Click to Ask):**")
    q_col1, q_col2, q_col3 = st.columns(3)
    
    preset_query = None
    with q_col1:
        if st.button("🚨 Which terminal is most likely to become congested?"):
            preset_query = "Which terminal is most likely to become congested?"
        if st.button("🔀 Which vessels should be rerouted?"):
            preset_query = "Which vessels should be rerouted?"
        if st.button("⚠️ Why is Terminal T2 high risk?"):
            preset_query = "Why is Terminal T2 high risk?"
    with q_col2:
        if st.button("⚓ Which vessel should get next available berth?"):
            preset_query = "Which vessel should get the next available berth?"
        if st.button("🏗️ How are cranes currently allocated?"):
            preset_query = "How are cranes currently allocated?"
        if st.button("⭐ Show highest-priority vessels next 12 hours"):
            preset_query = "Show me the highest-priority vessels for the next 12 hours."
    with q_col3:
        if st.button("📋 Generate summary of the next 72 hours"):
            preset_query = "Generate a summary of the next 72 hours."
        if st.button("🔍 Why was Vessel V104 assigned to Berth B3?"):
            preset_query = "Why was Vessel V104 assigned to Berth B301?"
        if st.button("🛑 What is the biggest operational bottleneck right now?"):
            preset_query = "What is the biggest operational bottleneck right now?"

    user_query = st.chat_input("Ask IBM Bob Copilot an operational question (e.g. 'Why is Terminal T2 high risk?')...")
    
    active_query = preset_query or user_query

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            {"role": "assistant", "content": "Hello Shift Supervisor! I am your **IBM Bob Port Operations Copilot**. I monitor vessel arrivals, detect congestion hotspots, and optimize berth and crane allocations. How can I assist your shift today?"}
        ]

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if active_query:
        st.session_state.chat_history.append({"role": "user", "content": active_query})
        with st.chat_message("user"):
            st.markdown(active_query)

        with st.chat_message("assistant"):
            with st.spinner("Consulting live optimization engine and IBM Bob agent..."):
                response = pipeline["bob_agent"].query(
                    question=active_query,
                    plan_df=plan_df,
                    hotspots=hotspots,
                    routing_recs=routing_recs,
                    kpi_metrics=kpis,
                    terminals_df=terminals_df,
                    vessels_df=vessels_df
                )
                
                resp_text = f"{response['answer']}\n\n"
                if response.get("reasoning"):
                    resp_text += f"**🧠 Operational Rationale**: {response['reasoning']}\n\n"
                if response.get("recommended_action"):
                    resp_text += f"**⚡ Recommended Action**: {response['recommended_action']}"

                st.markdown(resp_text)
                st.session_state.chat_history.append({"role": "assistant", "content": resp_text})
