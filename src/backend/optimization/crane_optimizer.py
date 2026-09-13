import pandas as pd
import numpy as np
from typing import Dict, List, Any

class CraneOptimizer:
    """
    Optimizes dynamic crane allocation (STS gantry cranes) per vessel call.
    Allocates 2 to 5 cranes based on container volume, vessel beam/LOA, and turnaround priority.
    """

    def __init__(self, base_productivity: float = 28.0):
        self.base_productivity = base_productivity

    def optimize_crane_assignments(
        self,
        berth_schedule_df: pd.DataFrame,
        cranes_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Assigns specific operational cranes to each scheduled vessel and computes
        accelerated discharge duration.
        """
        schedule = berth_schedule_df.copy()
        
        assigned_crane_counts = []
        assigned_crane_ids = []
        accelerated_durations = []
        crane_reasons = []

        operational_cranes = cranes_df[cranes_df["status"] == "OPERATIONAL"].copy()

        for _, row in schedule.iterrows():
            containers = row["containers"]
            priority = row["priority"]
            v_size = row["vessel_size"]
            term = row["assigned_terminal"]
            berth = row["assigned_berth"]

            # Available cranes at this terminal
            term_cranes = operational_cranes[operational_cranes["terminal_id"] == term]["crane_id"].tolist()
            max_available = len(term_cranes)

            # Determine target crane count based on workload & priority
            if v_size == "ULCV" or containers >= 2800:
                target_cranes = 5
            elif v_size == "POST_PANAMAX" or containers >= 1800:
                target_cranes = 4
            elif v_size == "PANAMAX" or containers >= 1100:
                target_cranes = 3
            else:
                target_cranes = 2

            # Priority boost: CRITICAL gets +1 crane if possible
            if priority == "CRITICAL" and target_cranes < 5:
                target_cranes += 1
            elif priority == "LOW" and target_cranes > 2:
                target_cranes -= 1

            # Cap by terminal availability
            allocated_count = max(2, min(target_cranes, max_available, 5))
            
            # Select specific cranes
            selected_cranes = term_cranes[:allocated_count]
            if len(selected_cranes) < allocated_count:
                selected_cranes = [f"CR-{term}-{i+1:02d}" for i in range(allocated_count)]

            # Effective moves/hour rate with multi-crane interference factor (e.g. 0.95 efficiency)
            efficiency = 1.0 - (allocated_count - 1) * 0.03
            effective_rate = allocated_count * self.base_productivity * efficiency
            
            # Recalculated accelerated duration
            opt_duration = round(containers / max(1.0, effective_rate), 2)

            reason = (
                f"Allocated {allocated_count} STS cranes ({', '.join(selected_cranes[:3])}...) "
                f"for {containers:,} container moves ({v_size} class, Priority: {priority}). "
                f"Achieves {round(effective_rate, 1)} moves/hr gross throughput."
            )

            assigned_crane_counts.append(allocated_count)
            assigned_crane_ids.append(", ".join(selected_cranes))
            accelerated_durations.append(opt_duration)
            crane_reasons.append(reason)

        schedule["cranes_allocated"] = assigned_crane_counts
        schedule["crane_ids"] = assigned_crane_ids
        schedule["optimized_service_duration"] = accelerated_durations
        schedule["crane_assignment_reason"] = crane_reasons

        # Update end time based on accelerated duration
        schedule["optimized_end_time"] = schedule["start_time"] + schedule["optimized_service_duration"]
        schedule["optimized_end_time"] = schedule["optimized_end_time"].round(2)

        return schedule
