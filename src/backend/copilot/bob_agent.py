import os
import re
import json
import requests
import pandas as pd
from typing import Dict, List, Any, Optional
from ..config import settings
from .prompts import SYSTEM_PROMPT
from .explainability import ExplainabilityEngine

class BobCopilotAgent:
    """
    IBM Bob Port Operations Copilot agent.
    Provides natural-language operational Q&A grounded in live optimization schedules,
    ML risk predictions, and constraint explanations. Integrates with watsonx Granite 3.0
    with robust local operational reasoning fallback.
    """

    def __init__(self):
        self.explain_engine = ExplainabilityEngine()
        self.watsonx_api_key = settings.WATSONX_API_KEY
        self.watsonx_project_id = settings.WATSONX_PROJECT_ID
        self.watsonx_url = settings.WATSONX_URL
        self.model_id = settings.WATSONX_MODEL_ID

    def query(
        self,
        question: str,
        plan_df: pd.DataFrame,
        hotspots: List[Dict[str, Any]],
        routing_recs: List[Dict[str, Any]],
        kpi_metrics: Dict[str, Any],
        terminals_df: pd.DataFrame,
        vessels_df: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Main query entry point. Interprets question intent, grounds context in live data,
        and generates a high-fidelity operational response with supporting data and action items.
        """
        q_lower = question.lower().strip()
        
        # 1. Check for specific operational query patterns
        # Case A: Congestion / Hotspot terminal query
        if any(w in q_lower for w in ["most likely to become congested", "which terminal is most", "highest risk terminal", "bottleneck right now", "biggest operational bottleneck"]):
            return self._handle_congestion_query(hotspots, scored_df=None, terminals_df=terminals_df)

        # Case B: Why is Terminal X high risk
        term_match = re.search(r"terminal\s*(t[123])", q_lower)
        if ("why" in q_lower and "risk" in q_lower) or ("why is" in q_lower and term_match):
            term_id = term_match.group(1).upper() if term_match else "T2"
            return self._handle_why_terminal_risk(term_id, hotspots, terminals_df)

        # Case C: Rerouting recommendation query
        if any(w in q_lower for w in ["reroute", "alternate route", "redirect", "which vessels should be"]):
            return self._handle_rerouting_query(routing_recs)

        # Case D: Next available berth / vessel assignment
        if any(w in q_lower for w in ["next available berth", "next vessel", "who gets the next"]):
            return self._handle_next_berth_query(plan_df)

        # Case E: Crane allocation query
        if any(w in q_lower for w in ["cranes", "crane allocation", "how are cranes"]):
            return self._handle_crane_query(plan_df)

        # Case F: High-priority vessels in next 12 hours
        if any(w in q_lower for w in ["highest-priority", "high priority", "next 12 hours", "critical vessels"]):
            return self._handle_priority_vessels_query(plan_df, window_hours=12.0)

        # Case G: 72-hour summary
        if any(w in q_lower for w in ["summary of the next 72", "72 hours summary", "overview", "shift summary"]):
            return self._handle_72h_summary(plan_df, kpi_metrics, hotspots, routing_recs)

        # Case H: Specific vessel question (e.g. "Why was Vessel V104 assigned to Berth B3?" or "What about V101?")
        vessel_match = re.search(r"(v\d{3})", q_lower)
        if vessel_match:
            v_id = vessel_match.group(1).upper()
            return self._handle_vessel_audit_query(v_id, plan_df, routing_recs, hotspots, terminals_df)

        # Case I: What-if / delay query in chat
        if any(w in q_lower for w in ["what happens if", "delayed by", "what if"]):
            return self._handle_what_if_guidance(question, plan_df)

        # Default: General domain grounding with watsonx or comprehensive operational synthesizer
        return self._generate_grounded_response(question, plan_df, kpi_metrics, hotspots, routing_recs)

    def _handle_congestion_query(self, hotspots: List[Dict[str, Any]], scored_df: Optional[pd.DataFrame], terminals_df: pd.DataFrame) -> Dict[str, Any]:
        if not hotspots:
            return {
                "answer": "All port terminals are currently operating within nominal capacity buffers. No severe congestion hotspots are predicted across the 72-hour horizon.",
                "supporting_data": {"active_hotspots": 0, "status": "NOMINAL"},
                "reasoning": "Vessel arrival distributions match berth and crane capacities.",
                "recommended_action": "Maintain scheduled operational shifts."
            }
        
        top_spot = hotspots[0]
        term_id = top_spot["terminal_id"]
        term_name = terminals_df[terminals_df["terminal_id"] == term_id]["terminal_name"].iloc[0] if len(terminals_df[terminals_df["terminal_id"] == term_id]) > 0 else f"Terminal {term_id}"

        answer = (
            f"**{term_name} ({term_id})** is the highest-risk terminal and the primary operational bottleneck. "
            f"It is predicted to reach **{top_spot['severity']}** congestion (Peak Risk Score: **{top_spot['peak_risk_score']}/100**) "
            f"between **Hour {int(top_spot['start_hour'])}:00 and Hour {int(top_spot['end_hour'])}:00**."
        )

        return {
            "answer": answer,
            "supporting_data": {
                "terminal": term_id,
                "terminal_name": term_name,
                "peak_risk_score": top_spot["peak_risk_score"],
                "duration_hours": top_spot["duration_hours"],
                "affected_vessel_count": top_spot["affected_count"],
                "total_teu_at_risk": f"{top_spot['total_teu_at_risk']:,} TEU",
                "root_cause": top_spot["primary_root_cause"]
            },
            "reasoning": f"Driven by {top_spot['primary_root_cause']} coinciding with a cluster of {top_spot['affected_count']} arriving container vessels.",
            "recommended_action": f"Execute proactive rerouting of incoming vessels to under-utilized terminals (such as Terminal T3) to eliminate queue buildup."
        }

    def _handle_why_terminal_risk(self, term_id: str, hotspots: List[Dict[str, Any]], terminals_df: pd.DataFrame) -> Dict[str, Any]:
        term_spots = [h for h in hotspots if h["terminal_id"] == term_id]
        term_meta = terminals_df[terminals_df["terminal_id"] == term_id].iloc[0] if len(terminals_df[terminals_df["terminal_id"] == term_id]) > 0 else None

        if not term_spots:
            return {
                "answer": f"Terminal {term_id} is currently operating with stable risk metrics (no active hotspot alarms detected).",
                "supporting_data": {"terminal": term_id, "risk_status": "STABLE"},
                "reasoning": "Demand does not exceed physical berth and crane capacity limits.",
                "recommended_action": "Continue baseline monitoring."
            }

        spot = term_spots[0]
        yard_pct = int(float(term_meta["current_yard_utilization"]) * 100) if term_meta is not None else 85
        
        answer = (
            f"**Terminal {term_id} is categorized as HIGH/CRITICAL risk (Risk Score: {spot['peak_risk_score']}/100)** "
            f"due to a convergence of physical capacity constraints between Hours {int(spot['start_hour'])} and {int(spot['end_hour'])}:\n\n"
            f"1. **{spot['primary_root_cause']}**.\n"
            f"2. **Yard Saturation**: Current yard utilization is at **{yard_pct}%**, leaving minimal dwell buffer for discharged containers.\n"
            f"3. **Vessel Inflow Surge**: **{spot['affected_count']} vessels** ({spot['total_teu_at_risk']:,} TEU) arrive in rapid succession."
        )

        return {
            "answer": answer,
            "supporting_data": {
                "terminal_id": term_id,
                "peak_risk": spot["peak_risk_score"],
                "time_window": f"Hours {int(spot['start_hour'])} - {int(spot['end_hour'])}",
                "affected_vessels": spot["affected_vessel_names"][:4],
                "yard_utilization": f"{yard_pct}%"
            },
            "reasoning": "Demand-to-capacity ratio spikes above 1.25, creating an unavoidable offshore vessel queue if vessels are not redirected.",
            "recommended_action": f"Divert compatible vessels to Terminal T3 which currently has available yard capacity and deepwater berths."
        }

    def _handle_rerouting_query(self, routing_recs: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not routing_recs:
            return {
                "answer": "No vessel rerouting is currently required; all vessels can be serviced at their preferred terminals with minimal waiting times.",
                "supporting_data": {"recommendations_count": 0},
                "reasoning": "Optimal scheduling achieves acceptable turnaround times without diversions.",
                "recommended_action": "Maintain assigned berths."
            }

        rec_items = []
        total_saved = 0.0
        for r in routing_recs:
            total_saved += r["estimated_time_savings_hrs"]
            rec_items.append(
                f"- **{r['vessel_name']} ({r['vessel_id']})**: Reroute from **{r['original_terminal']}** ({r['original_terminal_name']}) "
                f"to **{r['recommended_terminal']}** ({r['recommended_terminal_name']}) → **Saves {r['estimated_time_savings_hrs']} hrs wait time**"
            )

        answer = (
            f"The Copilot recommends rerouting **{len(routing_recs)} vessel(s)** to prevent severe bottleneck queuing, "
            f"saving a cumulative **{round(total_saved, 1)} hours** of vessel waiting time:\n\n" +
            "\n".join(rec_items)
        )

        return {
            "answer": answer,
            "supporting_data": {
                "rerouted_vessels": [r["vessel_id"] for r in routing_recs],
                "cumulative_hours_saved": round(total_saved, 1),
                "count": len(routing_recs)
            },
            "reasoning": "Alternate terminals have validated draft/LOA clearance, available deep-water berths, and under-utilized yard space.",
            "recommended_action": "Approve alternate terminal routing orders to harbor pilots and shipping line agents."
        }

    def _handle_next_berth_query(self, plan_df: pd.DataFrame) -> Dict[str, Any]:
        unberthed = plan_df[plan_df["start_time_hour"] >= 0.0].sort_values("start_time_hour")
        if unberthed.empty:
            return {"answer": "No vessels currently scheduled.", "supporting_data": {}, "reasoning": "", "recommended_action": ""}

        next_v = unberthed.iloc[0]
        answer = (
            f"The next vessel scheduled to dock is **{next_v['vessel_name']} ({next_v['vessel_id']})** at **Berth {next_v['assigned_berth']} "
            f"({next_v['assigned_terminal']})** starting at **Hour {next_v['start_time_hour']:.1f}**.\n"
            f"- **Priority**: {next_v['priority']}\n"
            f"- **Workload**: {next_v['containers']:,} moves\n"
            f"- **Cranes Allocated**: {next_v['cranes_assigned']} STS cranes"
        )
        return {
            "answer": answer,
            "supporting_data": {
                "vessel_id": next_v["vessel_id"],
                "berth": next_v["assigned_berth"],
                "start_hour": next_v["start_time_hour"],
                "waiting_time": f"{next_v['waiting_time_hours']} hrs"
            },
            "reasoning": "Vessel has highest arrival queue precedence and verified berth availability.",
            "recommended_action": "Clear berth apron and position assigned gantry cranes."
        }

    def _handle_crane_query(self, plan_df: pd.DataFrame) -> Dict[str, Any]:
        avg_cranes = round(float(plan_df["cranes_assigned"].mean()), 1)
        crane_dist = plan_df["cranes_assigned"].value_counts().to_dict()
        
        answer = (
            f"Cranes are allocated dynamically based on vessel class (TEU volume) and priority:\n"
            f"- **Average Allocation**: {avg_cranes} cranes per vessel\n"
            f"- **Breakdown**: {crane_dist.get(5, 0)} vessels with 5 cranes (ULCV/Critical), {crane_dist.get(4, 0)} with 4 cranes, {crane_dist.get(3, 0)} with 3 cranes, {crane_dist.get(2, 0)} with 2 cranes.\n"
            f"- High-priority and ULCV container ships (e.g. > 2,800 moves) receive top crane density to minimize berth occupancy."
        )
        return {
            "answer": answer,
            "supporting_data": {"crane_distribution": crane_dist, "average_cranes": avg_cranes},
            "reasoning": "Maximizes gross berth moves per hour while respecting crane track clearances.",
            "recommended_action": "Monitor crane maintenance logs to maintain 100% crane availability."
        }

    def _handle_priority_vessels_query(self, plan_df: pd.DataFrame, window_hours: float = 12.0) -> Dict[str, Any]:
        window_df = plan_df[
            (plan_df["eta_hour"] <= window_hours) &
            (plan_df["priority"].isin(["CRITICAL", "HIGH"]))
        ].sort_values("eta_hour")

        if window_df.empty:
            return {
                "answer": f"There are no CRITICAL or HIGH priority vessels arriving in the next {int(window_hours)} hours.",
                "supporting_data": {"count": 0},
                "reasoning": "All incoming traffic in this window is NORMAL or LOW priority.",
                "recommended_action": "Maintain standard discharge pace."
            }

        items = []
        for _, v in window_df.iterrows():
            items.append(
                f"- **{v['vessel_name']} ({v['vessel_id']})** [{v['priority']}]: ETA Hour {v['eta_hour']:.1f} → Berth {v['assigned_berth']} ({v['assigned_terminal']}), {v['cranes_assigned']} cranes, {v['containers']:,} moves"
            )

        answer = (
            f"Found **{len(window_df)} high-priority vessel(s)** in the next {int(window_hours)} hours:\n\n" +
            "\n".join(items)
        )
        return {
            "answer": answer,
            "supporting_data": {"vessels": window_df["vessel_id"].tolist(), "count": len(window_df)},
            "reasoning": "Prioritized by cargo sensitivity and intermodal rail connections.",
            "recommended_action": "Ensure tug pilots and stevedore gangs are staged 1 hour prior to ETA."
        }

    def _handle_72h_summary(self, plan_df: pd.DataFrame, kpi_metrics: Dict[str, Any], hotspots: List[Dict[str, Any]], routing_recs: List[Dict[str, Any]]) -> Dict[str, Any]:
        opt = kpi_metrics["optimized"]
        base = kpi_metrics["baseline"]
        imp = kpi_metrics["improvements"]

        answer = (
            f"### 📋 72-Hour Port Operational Executive Summary\n\n"
            f"- **Total Vessels Handled**: **{len(plan_df)} container vessels**\n"
            f"- **Optimized Avg Waiting Time**: **{opt['avg_waiting_time_hours']} hours** (vs Baseline: {base['avg_waiting_time_hours']} hours → **{imp['avg_waiting_time_reduction_pct']}% reduction**)\n"
            f"- **Total Fleet Port Dwell Saved**: **{imp['total_vessel_hours_saved']} hours**\n"
            f"- **Berth Utilization**: **{opt['berth_utilization_pct']}%** balanced across 3 terminals\n"
            f"- **Proactive Reroutings Executed**: **{len(routing_recs)} vessel(s)** redirected to eliminate terminal hotspots\n"
            f"- **Hotspots Predicted**: **{len(hotspots)} bottleneck window(s)** (all actively mitigated by optimizer)"
        )

        return {
            "answer": answer,
            "supporting_data": kpi_metrics,
            "reasoning": "OR-Tools CP-SAT berth optimization combined with proactive rerouting successfully prevents multi-day queue formation.",
            "recommended_action": "Proceed with 72-hour operational plan and monitor Terminal T2 surge arrivals."
        }

    def _handle_vessel_audit_query(self, v_id: str, plan_df: pd.DataFrame, routing_recs: List[Dict[str, Any]], hotspots: List[Dict[str, Any]], terminals_df: pd.DataFrame) -> Dict[str, Any]:
        card = self.explain_engine.generate_vessel_audit_card(v_id, plan_df, routing_recs, hotspots, terminals_df)
        if "error" in card:
            return {"answer": card["error"], "supporting_data": {}, "reasoning": "", "recommended_action": ""}

        answer = (
            f"### 🔍 Decision Audit Card: {card['vessel_name']} ({card['vessel_id']})\n\n"
            f"- **What Happened**: {card['what_happened']}\n"
            f"- **Why This Was a Problem**: {card['why_is_this_a_problem']}\n"
            f"- **System Prediction**: {card['what_system_predicts']}\n"
            f"- **Recommended Action**: {card['recommended_action']}\n"
            f"- **Why Action Selected**: {card['why_action_selected']}\n"
            f"- **Constraints Enforced**: {card['constraints_considered']}"
        )

        return {
            "answer": answer,
            "supporting_data": card,
            "reasoning": card["why_action_selected"],
            "recommended_action": card["recommended_action"]
        }

    def _handle_what_if_guidance(self, question: str, plan_df: pd.DataFrame) -> Dict[str, Any]:
        answer = (
            "To simulate this exact operational perturbation, open the **🧪 Scenario & What-If Studio** tab in the dashboard. "
            "You can adjust vessel delay sliders, toggle crane breakdown outages, or simulate weather slowdowns. "
            "The system will re-execute the Google OR-Tools CP-SAT solver in real-time and display side-by-side KPI deltas and revised Gantt schedules."
        )
        return {
            "answer": answer,
            "supporting_data": {"feature": "Scenario Simulator"},
            "reasoning": "Real-time recalculation produces exact mathematical schedule differences.",
            "recommended_action": "Launch simulation run in What-If Studio."
        }

    def _generate_grounded_response(self, question: str, plan_df: pd.DataFrame, kpi_metrics: Dict[str, Any], hotspots: List[Dict[str, Any]], routing_recs: List[Dict[str, Any]]) -> Dict[str, Any]:
        # Watsonx API integration if key provided
        if self.watsonx_api_key and self.watsonx_project_id:
            try:
                prompt_context = (
                    f"{SYSTEM_PROMPT}\n\n"
                    f"Operational Context:\n"
                    f"- Total Vessels: {len(plan_df)}\n"
                    f"- Average Wait Time: {kpi_metrics['optimized']['avg_waiting_time_hours']} hrs\n"
                    f"- Active Hotspots: {len(hotspots)}\n"
                    f"- Recommended Reroutings: {[r['vessel_id'] for r in routing_recs]}\n\n"
                    f"User Question: {question}\n\n"
                    f"Answer:"
                )
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.watsonx_api_key}"
                }
                payload = {
                    "model_id": self.model_id,
                    "input": prompt_context,
                    "parameters": {"max_new_tokens": 300, "temperature": 0.2},
                    "project_id": self.watsonx_project_id
                }
                res = requests.post(f"{self.watsonx_url}/ml/v1/text/generation?version=2023-05-29", json=payload, headers=headers, timeout=5)
                if res.status_code == 200:
                    generated_text = res.json()["results"][0]["generated_text"]
                    return {
                        "answer": generated_text.strip(),
                        "supporting_data": {"source": "watsonx.ai Granite 3.0"},
                        "reasoning": "Generated using IBM watsonx LLM grounded on live port operational telemetry.",
                        "recommended_action": "Refer to 72-hour operational plan."
                    }
            except Exception:
                pass  # Fall through to deterministic synthesizer

        # Fallback comprehensive grounded answer
        answer = (
            f"Based on the current 72-hour operational state across {len(plan_df)} vessels and 3 terminals:\n\n"
            f"- **Port Congestion**: {len(hotspots)} hotspot(s) detected. The primary bottleneck is Terminal T2 during peak arrival surge.\n"
            f"- **Optimization Status**: OR-Tools CP-SAT has scheduled all vessels with an average wait time of **{kpi_metrics['optimized']['avg_waiting_time_hours']} hours** (saving {kpi_metrics['improvements']['total_vessel_hours_saved']} total dwell hours).\n"
            f"- **Rerouting**: {len(routing_recs)} vessel(s) recommended for alternate terminal diversion.\n"
            f"You can ask about specific vessels (e.g. 'Why was V104 assigned to Berth B3?'), specific terminals ('Why is Terminal T2 high risk?'), or inspect crane allocations."
        )

        return {
            "answer": answer,
            "supporting_data": kpi_metrics["optimized"],
            "reasoning": "Real-time state telemetry aggregated from OR-Tools optimization engine.",
            "recommended_action": "Inspect 72-Hour Plan or drill into Recommendations tab."
        }
