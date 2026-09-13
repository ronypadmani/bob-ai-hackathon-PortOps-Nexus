import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional

class OperationalPlanGenerator:
    """
    Generates a unified, rolling 72-hour master operational plan for port shift supervisors.
    Combines berth allocations, crane assignments, rerouting decisions, and risk indicators.
    """

    def __init__(self, horizon_hours: int = 72):
        self.horizon_hours = horizon_hours

    def generate_72h_plan(
        self,
        optimized_schedule_df: pd.DataFrame,
        routing_recommendations: List[Dict[str, Any]],
        scored_features_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Builds the detailed 72-hour operational plan table.
        """
        recs_map = {r["vessel_id"]: r for r in routing_recommendations}
        plan_rows = []

        for _, row in optimized_schedule_df.iterrows():
            v_id = row["vessel_id"]
            start_h = row["start_time"]
            end_h = row.get("optimized_end_time", row["end_time"])
            term = row["assigned_terminal"]
            
            # Find terminal risk at arrival and start times
            risk_rows = scored_features_df[
                (scored_features_df["terminal_id"] == term) &
                (scored_features_df["hour"] == int(min(71, start_h)))
            ]
            risk_score = float(risk_rows["risk_score"].iloc[0]) if len(risk_rows) > 0 else 30.0
            risk_category = risk_rows["risk_category"].iloc[0] if len(risk_rows) > 0 else "LOW"

            rerouted = v_id in recs_map
            rec_data = recs_map.get(v_id)
            routing_status = "REROUTED (RECOMMENDED)" if rerouted else "STANDARD ROUTE"

            plan_rows.append({
                "vessel_id": v_id,
                "vessel_name": row["vessel_name"],
                "vessel_size": row["vessel_size"],
                "priority": row["priority"],
                "containers": row["containers"],
                "cargo_volume_teu": row["cargo_volume"],
                "eta_hour": row["arrival_time"],
                "assigned_terminal": term,
                "assigned_berth": row["assigned_berth"],
                "start_time_hour": start_h,
                "end_time_hour": end_h,
                "duration_hours": round(end_h - start_h, 2),
                "waiting_time_hours": row["waiting_time_hours"],
                "cranes_assigned": row.get("cranes_allocated", 3),
                "crane_ids": row.get("crane_ids", "N/A"),
                "routing_status": routing_status,
                "routing_note": rec_data["reasoning"] if rerouted else "Operating at preferred terminal.",
                "terminal_risk_at_berth": risk_category,
                "risk_score": risk_score,
                "action_required": "PROCEED" if row["waiting_time_hours"] < 2.0 else "MONITOR QUEUE"
            })

        plan_df = pd.DataFrame(plan_rows).sort_values("start_time_hour").reset_index(drop=True)
        return plan_df
