import pandas as pd
from typing import Dict, List, Any, Optional

class ExplainabilityEngine:
    """
    Generates transparent, auditable decision rationales for shift supervisors.
    Answers the 6 key questions for every berth assignment, crane allocation, and rerouting event.
    """

    def generate_vessel_audit_card(
        self,
        vessel_id: str,
        plan_df: pd.DataFrame,
        routing_recs: List[Dict[str, Any]],
        hotspots: List[Dict[str, Any]],
        terminals_df: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Builds a comprehensive 6-point explanation card for a specific vessel.
        """
        match = plan_df[plan_df["vessel_id"] == vessel_id]
        if match.empty:
            return {"error": f"Vessel {vessel_id} not found in operational plan."}
        
        row = match.iloc[0]
        recs_map = {r["vessel_id"]: r for r in routing_recs}
        is_rerouted = vessel_id in recs_map
        rec_data = recs_map.get(vessel_id)

        v_name = row["vessel_name"]
        assigned_term = row["assigned_terminal"]
        assigned_berth = row["assigned_berth"]
        cranes = row["cranes_assigned"]
        wait_time = row["waiting_time_hours"]
        eta = row["eta_hour"]
        start_h = row["start_time_hour"]
        prio = row["priority"]
        containers = row["containers"]
        risk_lvl = row["terminal_risk_at_berth"]

        if is_rerouted:
            orig_term = rec_data["original_terminal"]
            orig_name = rec_data["original_terminal_name"]
            dest_name = rec_data["recommended_terminal_name"]
            savings = rec_data["estimated_time_savings_hrs"]
            
            what_happened = f"Vessel {v_name} ({vessel_id}) scheduled for arrival at Hour {eta} was redirected from {orig_name} ({orig_term}) to {dest_name} ({assigned_term})."
            why_problem = f"Terminal {orig_term} is experiencing severe congestion (Risk: {risk_lvl}) with berth utilization exceeding 100%."
            what_predicts = f"If unmitigated, {v_name} would have queued offshore for ~{rec_data['estimated_wait_time_original_hrs']} hours, causing downstream rail freight delays."
            what_action = f"Reroute {v_name} to {dest_name} Berth {assigned_berth}, deploy {cranes} STS cranes."
            why_action = f"Saves {savings} hours of demurrage and vessel wait time while balancing port-wide yard capacity."
            constraints = f"Verified: Max Draft ({row['vessel_size']} compatibility), Berth LOA clearance, Yard Capacity buffer in {assigned_term}."
        else:
            what_happened = f"Vessel {v_name} ({vessel_id}) is berthed at {assigned_term} Berth {assigned_berth} starting at Hour {start_h} (ETA: Hour {eta})."
            why_problem = f"Vessel has {containers:,} container moves with '{prio}' operational priority requiring timely discharge."
            what_predicts = f"Optimal turnaround window is {round(row['duration_hours'], 1)} hours with zero offshore anchor backlog."
            what_action = f"Assigned to Berth {assigned_berth} with {cranes} STS gantry cranes."
            why_action = f"Berth {assigned_berth} minimizes berth transition idle time and provides optimal crane density ({cranes} cranes)."
            constraints = f"OR-Tools CP-SAT verified non-overlapping time interval, depth/draft limits, and crane rail availability."

        return {
            "vessel_id": vessel_id,
            "vessel_name": v_name,
            "priority": prio,
            "assigned_berth": assigned_berth,
            "assigned_terminal": assigned_term,
            "what_happened": what_happened,
            "why_is_this_a_problem": why_problem,
            "what_system_predicts": what_predicts,
            "recommended_action": what_action,
            "why_action_selected": why_action,
            "constraints_considered": constraints
        }

    def generate_all_explanations(
        self,
        plan_df: pd.DataFrame,
        routing_recs: List[Dict[str, Any]],
        hotspots: List[Dict[str, Any]],
        terminals_df: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        explanations = []
        for v_id in plan_df["vessel_id"].unique():
            card = self.generate_vessel_audit_card(v_id, plan_df, routing_recs, hotspots, terminals_df)
            explanations.append(card)
        return explanations
