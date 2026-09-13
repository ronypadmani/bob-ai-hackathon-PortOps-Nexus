import pandas as pd
import numpy as np
from typing import Dict, Any

class PortMetricsCalculator:
    """
    Computes rigorous operational Key Performance Indicators (KPIs) comparing
    the unoptimized Baseline (reactive FIFO, static 3-crane allocation, no rerouting)
    against the AI & OR-Tools Optimized Operational Plan.
    """

    def compute_baseline_plan(
        self,
        vessels_df: pd.DataFrame,
        berths_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Simulates naive FIFO scheduling at preferred terminals without proactive rerouting.
        """
        baseline_records = []
        terminals = vessels_df["preferred_terminal"].unique()
        
        for term in terminals:
            term_vessels = vessels_df[vessels_df["preferred_terminal"] == term].sort_values("arrival_time")
            term_berths = berths_df[(berths_df["terminal_id"] == term) & (berths_df["status"] == "ACTIVE")]
            num_berths = max(1, len(term_berths))
            berth_ids = term_berths["berth_id"].tolist() or [f"B_{term}_1"]

            # Track availability clock per berth
            berth_clocks = {b: 0.0 for b in berth_ids}

            for _, v in term_vessels.iterrows():
                arr = float(v["arrival_time"])
                base_duration = float(v["service_duration"])
                
                # Assign to the earliest available berth
                earliest_berth = min(berth_clocks, key=berth_clocks.get)
                start = max(arr, berth_clocks[earliest_berth])
                end = start + base_duration
                wait = round(start - arr, 2)
                
                berth_clocks[earliest_berth] = end

                baseline_records.append({
                    "vessel_id": v["vessel_id"],
                    "vessel_name": v["vessel_name"],
                    "terminal_id": term,
                    "berth_id": earliest_berth,
                    "arrival_time": arr,
                    "start_time": start,
                    "end_time": end,
                    "duration": base_duration,
                    "waiting_time_hours": wait,
                    "priority": v["priority"]
                })

        return pd.DataFrame(baseline_records).sort_values("start_time").reset_index(drop=True)

    def calculate_comparative_kpis(
        self,
        baseline_df: pd.DataFrame,
        optimized_df: pd.DataFrame,
        berths_df: pd.DataFrame,
        horizon_hours: int = 72
    ) -> Dict[str, Any]:
        """
        Computes accurate delta metrics between Baseline and Optimized plans.
        """
        base_avg_wait = float(baseline_df["waiting_time_hours"].mean())
        base_max_wait = float(baseline_df["waiting_time_hours"].max())
        base_total_dwell = float((baseline_df["end_time"] - baseline_df["arrival_time"]).sum())
        base_delayed_vessels = int((baseline_df["waiting_time_hours"] > 3.0).sum())

        opt_wait_col = "waiting_time_hours"
        opt_avg_wait = float(optimized_df[opt_wait_col].mean())
        opt_max_wait = float(optimized_df[opt_wait_col].max())
        opt_end_col = "end_time_hour" if "end_time_hour" in optimized_df.columns else "end_time"
        opt_arr_col = "eta_hour" if "eta_hour" in optimized_df.columns else "arrival_time"
        opt_total_dwell = float((optimized_df[opt_end_col] - optimized_df[opt_arr_col]).sum())
        opt_delayed_vessels = int((optimized_df[opt_wait_col] > 3.0).sum())

        # Improvements
        wait_reduction_pct = round(((base_avg_wait - opt_avg_wait) / max(0.01, base_avg_wait)) * 100, 1) if base_avg_wait > 0 else 0.0
        max_wait_reduction_pct = round(((base_max_wait - opt_max_wait) / max(0.01, base_max_wait)) * 100, 1) if base_max_wait > 0 else 0.0
        dwell_reduction_pct = round(((base_total_dwell - opt_total_dwell) / max(0.01, base_total_dwell)) * 100, 1)

        # Berth utilization across 72h horizon
        total_berth_hours_available = len(berths_df[berths_df["status"] == "ACTIVE"]) * horizon_hours
        base_occupied_hours = float(baseline_df["duration"].sum())
        opt_duration_col = "duration_hours" if "duration_hours" in optimized_df.columns else "duration"
        opt_occupied_hours = float(optimized_df[opt_duration_col].sum())

        base_berth_util = round((base_occupied_hours / max(1.0, total_berth_hours_available)) * 100, 1)
        opt_berth_util = round((opt_occupied_hours / max(1.0, total_berth_hours_available)) * 100, 1)

        rerouted_count = int(optimized_df["routing_status"].str.contains("REROUTED").sum()) if "routing_status" in optimized_df.columns else 0

        return {
            "baseline": {
                "avg_waiting_time_hours": round(base_avg_wait, 2),
                "max_waiting_time_hours": round(base_max_wait, 2),
                "total_port_dwell_hours": round(base_total_dwell, 1),
                "delayed_vessels_count": base_delayed_vessels,
                "berth_utilization_pct": min(100.0, base_berth_util),
            },
            "optimized": {
                "avg_waiting_time_hours": round(opt_avg_wait, 2),
                "max_waiting_time_hours": round(opt_max_wait, 2),
                "total_port_dwell_hours": round(opt_total_dwell, 1),
                "delayed_vessels_count": opt_delayed_vessels,
                "berth_utilization_pct": min(100.0, opt_berth_util),
                "rerouted_vessels_count": rerouted_count,
            },
            "improvements": {
                "avg_waiting_time_reduction_pct": wait_reduction_pct,
                "max_waiting_time_reduction_pct": max_wait_reduction_pct,
                "total_dwell_reduction_pct": dwell_reduction_pct,
                "total_vessel_hours_saved": round(base_total_dwell - opt_total_dwell, 1),
                "congested_vessels_mitigated": base_delayed_vessels - opt_delayed_vessels
            }
        }
