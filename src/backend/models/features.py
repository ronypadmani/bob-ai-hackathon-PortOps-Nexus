import pandas as pd
import numpy as np
from typing import Dict, List, Tuple

class PortFeatureEngineer:
    """
    Extracts temporal sliding window features, capacity utilization profiles,
    and queue pressure indices across the 72-hour planning horizon for each terminal.
    """

    def __init__(self, horizon_hours: int = 72, time_step_hours: int = 1):
        self.horizon_hours = horizon_hours
        self.time_step_hours = time_step_hours

    def extract_terminal_hourly_features(
        self,
        vessels_df: pd.DataFrame,
        berths_df: pd.DataFrame,
        cranes_df: pd.DataFrame,
        terminals_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Generates an hourly time-series dataset for each terminal capturing:
        - Arriving vessel count
        - Active in-window vessel demand
        - Total container workload required
        - Total available berth hours
        - Total operational crane capacity (moves/hour)
        - Demand-to-Capacity ratio
        - Yard utilization buffer
        """
        records = []
        terminals = terminals_df["terminal_id"].unique()
        hours = np.arange(0, self.horizon_hours, self.time_step_hours)

        for term in terminals:
            term_meta = terminals_df[terminals_df["terminal_id"] == term].iloc[0]
            term_berths = berths_df[berths_df["terminal_id"] == term]
            term_cranes = cranes_df[cranes_df["terminal_id"] == term]
            
            num_berths = len(term_berths[term_berths["status"] == "ACTIVE"])
            active_cranes = term_cranes[term_cranes["status"] == "OPERATIONAL"]
            total_crane_rate = (active_cranes["capacity"] * active_cranes["availability"]).sum()
            yard_util = float(term_meta["current_yard_utilization"])

            for h in hours:
                h_start = float(h)
                h_end = h_start + self.time_step_hours
                
                # Window 4-hour forward lookahead
                lookahead_4h = h_start + 4.0
                
                # Vessels assigned/preferred to this terminal
                term_vessels = vessels_df[vessels_df["preferred_terminal"] == term]
                
                # Arriving exactly in this hour
                arriving_vessels = term_vessels[
                    (term_vessels["arrival_time"] >= h_start) & 
                    (term_vessels["arrival_time"] < h_end)
                ]
                
                # Vessels overlapping with lookahead window [h_start, lookahead_4h]
                # Assuming naive arrival-to-completion window
                window_vessels = term_vessels[
                    (term_vessels["arrival_time"] <= lookahead_4h) &
                    (term_vessels["arrival_time"] + term_vessels["service_duration"] >= h_start)
                ]

                num_arriving = len(arriving_vessels)
                active_vessels_count = len(window_vessels)
                total_workload_moves = window_vessels["containers"].sum()
                
                # High-priority vessels in window
                crit_vessels = len(window_vessels[window_vessels["priority"].isin(["CRITICAL", "HIGH"])])
                
                # Capacity calculations
                available_berth_hours = num_berths * self.time_step_hours
                available_crane_moves = total_crane_rate * self.time_step_hours
                
                # Demand vs capacity indices
                berth_pressure_ratio = active_vessels_count / max(1, num_berths)
                # Crane moves required per hour across active vessels vs crane supply
                crane_pressure_ratio = (total_workload_moves / max(1, active_vessels_count * 12)) / max(1.0, available_crane_moves) if active_vessels_count > 0 else 0.0
                
                # Dynamic yard load proxy based on container workload & initial yard util
                projected_yard_util = min(1.0, yard_util + (total_workload_moves / max(1000, term_meta["yard_capacity"])) * 0.1)

                records.append({
                    "terminal_id": term,
                    "hour": h_start,
                    "num_arriving": num_arriving,
                    "active_vessels_count": active_vessels_count,
                    "crit_vessels": crit_vessels,
                    "total_workload_moves": total_workload_moves,
                    "available_berths": num_berths,
                    "total_crane_rate": total_crane_rate,
                    "berth_pressure_ratio": round(berth_pressure_ratio, 2),
                    "crane_pressure_ratio": round(crane_pressure_ratio, 2),
                    "yard_utilization": round(projected_yard_util, 3),
                    "is_bottleneck": 1 if (berth_pressure_ratio > 1.0 or projected_yard_util > 0.88 or crane_pressure_ratio > 1.1) else 0
                })

        return pd.DataFrame(records)

    def extract_vessel_features(self, vessels_df: pd.DataFrame, terminals_df: pd.DataFrame) -> pd.DataFrame:
        """
        Extracts individual vessel risk features for prioritization.
        """
        df = vessels_df.copy()
        
        priority_map = {"CRITICAL": 4, "HIGH": 3, "NORMAL": 2, "LOW": 1}
        df["priority_num"] = df["priority"].map(priority_map).fillna(2)
        
        # Merge terminal baseline yard pressure
        term_map = terminals_df.set_index("terminal_id")["current_yard_utilization"].to_dict()
        df["terminal_initial_yard_util"] = df["preferred_terminal"].map(term_map).fillna(0.75)
        
        # Workload intensity = containers / length
        df["workload_intensity"] = df["containers"] / df["length_overall"]
        
        return df
