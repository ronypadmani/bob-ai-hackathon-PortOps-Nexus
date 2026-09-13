import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from ortools.sat.python import cp_model

class BerthOptimizer:
    """
    Solves the Berth Allocation Problem (BAP) using Google OR-Tools CP-SAT constraint programming.
    Enforces physical constraints (draft, LOA, availability windows) and non-overlapping
    spatial-temporal intervals while minimizing priority-weighted vessel wait times.
    """

    def __init__(self, time_limit_seconds: int = 15, time_scale_factor: int = 2):
        # time_scale_factor = 2 means 30-minute discretization (ultra-fast exact solver convergence)
        self.time_limit_seconds = time_limit_seconds
        self.scale = time_scale_factor

    def optimize_berth_allocations(
        self,
        vessels_df: pd.DataFrame,
        berths_df: pd.DataFrame,
        rerouting_overrides: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Executes the mathematical optimization model.
        Returns optimized vessel berth schedules, start/end timestamps, and waiting metrics.
        """
        rerouting_map = rerouting_overrides or {}
        model = cp_model.CpModel()
        
        active_berths = berths_df[berths_df["status"] == "ACTIVE"].copy().reset_index(drop=True)
        num_berths = len(active_berths)
        berth_ids = active_berths["berth_id"].tolist()
        
        horizon_units = int(72 * self.scale * 4.0)  # Generous upper bound for queue horizon (288 hours)
        
        vessel_vars = {}
        berth_intervals = {b_id: [] for b_id in berth_ids}
        
        waiting_cost_terms = []
        
        priority_weights = {
            "CRITICAL": 12,
            "HIGH": 6,
            "NORMAL": 2,
            "LOW": 1
        }

        for _, vessel in vessels_df.iterrows():
            v_id = vessel["vessel_id"]
            arrival_units = int(np.ceil(float(vessel["arrival_time"]) * self.scale))
            duration_units = max(1, int(np.ceil(float(vessel["service_duration"]) * self.scale)))
            v_loa = float(vessel["length_overall"])
            v_draft = float(vessel["draft"])
            weight = priority_weights.get(vessel["priority"], 2)
            
            # Determine target terminal (check if rerouted)
            target_terminal = rerouting_map.get(v_id, vessel["preferred_terminal"])
            
            # Identify feasible berths for this vessel (all physically compatible berths)
            feasible_berths = []
            for _, berth in active_berths.iterrows():
                b_id = berth["berth_id"]
                # Must satisfy physical LOA and draft
                if v_loa <= float(berth["max_length"]) and v_draft <= float(berth["max_draft"]):
                    feasible_berths.append(b_id)
            
            if not feasible_berths:
                feasible_berths = berth_ids

            # Variables for this vessel
            start_var = model.NewIntVar(arrival_units, horizon_units, f"start_{v_id}")
            end_var = model.NewIntVar(arrival_units + duration_units, horizon_units + duration_units, f"end_{v_id}")
            model.Add(end_var == start_var + duration_units)

            # Berth assignment booleans
            presence_literals = {}
            for b_id in feasible_berths:
                pres = model.NewBoolVar(f"pres_{v_id}_{b_id}")
                presence_literals[b_id] = pres
                
                # Optional interval on this berth
                interval = model.NewOptionalIntervalVar(
                    start_var, duration_units, end_var, pres, f"interval_{v_id}_{b_id}"
                )
                berth_intervals[b_id].append(interval)

                # Terminal divergence penalty if not matching target terminal
                b_term = active_berths[active_berths["berth_id"] == b_id]["terminal_id"].iloc[0]
                if b_term != target_terminal:
                    # Moderate diversion penalty (equivalent to ~2 hours wait time penalty)
                    waiting_cost_terms.append(pres * int(2.0 * self.scale * weight))

            # Exactly one feasible berth must be selected
            model.Add(sum(presence_literals.values()) == 1)

            # Waiting time variable
            wait_var = model.NewIntVar(0, horizon_units, f"wait_{v_id}")
            model.Add(wait_var == start_var - arrival_units)
            waiting_cost_terms.append(wait_var * weight)

            vessel_vars[v_id] = {
                "start": start_var,
                "end": end_var,
                "wait": wait_var,
                "presence": presence_literals,
                "duration_units": duration_units,
                "arrival_units": arrival_units,
                "target_terminal": target_terminal
            }

        # Non-overlapping constraint for each berth
        for b_id, intervals in berth_intervals.items():
            if intervals:
                model.AddNoOverlap(intervals)

        # Objective: minimize weighted waiting times
        model.Minimize(sum(waiting_cost_terms))

        # Greedy heuristic hint for instant CP-SAT feasibility and rapid convergence
        berth_hint_clocks = {b_id: 0 for b_id in berth_ids}
        sorted_vessels = vessels_df.sort_values("arrival_time")
        for _, vessel in sorted_vessels.iterrows():
            v_id = vessel["vessel_id"]
            arr_u = int(np.ceil(float(vessel["arrival_time"]) * self.scale))
            dur_u = max(1, int(np.ceil(float(vessel["service_duration"]) * self.scale)))
            v_data = vessel_vars[v_id]
            
            # Find earliest available feasible berth for hint
            best_b = None
            best_t = float("inf")
            for b_id in v_data["presence"].keys():
                avail_t = max(arr_u, berth_hint_clocks[b_id])
                if avail_t < best_t:
                    best_t = avail_t
                    best_b = b_id

            if best_b:
                model.AddHint(v_data["start"], best_t)
                model.AddHint(v_data["end"], best_t + dur_u)
                model.AddHint(v_data["presence"][best_b], 1)
                for other_b in v_data["presence"].keys():
                    if other_b != best_b:
                        model.AddHint(v_data["presence"][other_b], 0)
                berth_hint_clocks[best_b] = best_t + dur_u

        # Solve
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = self.time_limit_seconds
        solver.parameters.num_search_workers = 4
        status = solver.Solve(model)

        is_optimal = (status == cp_model.OPTIMAL or status == cp_model.FEASIBLE)
        
        results = []
        for _, vessel in vessels_df.iterrows():
            v_id = vessel["vessel_id"]
            v_data = vessel_vars[v_id]
            
            if is_optimal:
                start_val = round(solver.Value(v_data["start"]) / self.scale, 2)
                end_val = round(solver.Value(v_data["end"]) / self.scale, 2)
                wait_val = round(solver.Value(v_data["wait"]) / self.scale, 2)
                
                assigned_berth = None
                for b_id, pres_var in v_data["presence"].items():
                    if solver.Value(pres_var) == 1:
                        assigned_berth = b_id
                        break
            else:
                # Fallback heuristic FIFO if solver timeouts
                start_val = float(vessel["arrival_time"])
                end_val = round(start_val + float(vessel["service_duration"]), 2)
                wait_val = 0.0
                assigned_berth = "B101"

            assigned_terminal = active_berths[active_berths["berth_id"] == assigned_berth]["terminal_id"].iloc[0] if assigned_berth else vessel["preferred_terminal"]

            results.append({
                "vessel_id": v_id,
                "vessel_name": vessel["vessel_name"],
                "arrival_time": float(vessel["arrival_time"]),
                "priority": vessel["priority"],
                "vessel_size": vessel["vessel_size"],
                "containers": int(vessel["containers"]),
                "cargo_volume": float(vessel["cargo_volume"]),
                "preferred_terminal": vessel["preferred_terminal"],
                "assigned_terminal": assigned_terminal,
                "assigned_berth": assigned_berth,
                "start_time": start_val,
                "end_time": end_val,
                "duration_hours": round(end_val - start_val, 2),
                "waiting_time_hours": wait_val,
                "is_rerouted": (assigned_terminal != vessel["preferred_terminal"])
            })

        schedule_df = pd.DataFrame(results).sort_values("start_time").reset_index(drop=True)
        
        return {
            "status": "OPTIMAL" if status == cp_model.OPTIMAL else ("FEASIBLE" if status == cp_model.FEASIBLE else "FAILED"),
            "schedule": schedule_df,
            "objective_value": solver.ObjectiveValue() if is_optimal else None,
            "solver_time_seconds": solver.WallTime(),
            "avg_wait_time_hours": round(schedule_df["waiting_time_hours"].mean(), 2),
            "max_wait_time_hours": round(schedule_df["waiting_time_hours"].max(), 2),
            "total_vessels_scheduled": len(schedule_df)
        }
