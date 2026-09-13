import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional

class AlternateRoutingEngine:
    """
    Evaluates port congestion hotspots and recommends optimal vessel rerouting
    between terminals based on physical constraints (draft, LOA, berth depth),
    yard capacity headroom, and estimated queue reduction.
    """

    def __init__(self, congestion_threshold: float = 60.0):
        self.congestion_threshold = congestion_threshold

    def evaluate_routing_recommendations(
        self,
        vessels_df: pd.DataFrame,
        terminals_df: pd.DataFrame,
        berths_df: pd.DataFrame,
        hotspots: List[Dict[str, Any]],
        scored_features_df: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """
        Identifies vessels at risk in congested terminals and finds optimal feasible alternatives.
        """
        recommendations = []
        terminal_map = terminals_df.set_index("terminal_id").to_dict(orient="index")
        
        # Build berth physical limits per terminal
        term_berth_limits = {}
        for term_id in terminals_df["terminal_id"].unique():
            t_berths = berths_df[(berths_df["terminal_id"] == term_id) & (berths_df["status"] == "ACTIVE")]
            term_berth_limits[term_id] = {
                "max_draft": t_berths["max_draft"].max() if len(t_berths) > 0 else 0.0,
                "max_length": t_berths["max_length"].max() if len(t_berths) > 0 else 0.0,
                "berth_count": len(t_berths)
            }

        # Check vessels scheduled at congested terminals during hotspot windows
        for spot in hotspots:
            if spot["peak_risk_score"] < self.congestion_threshold:
                continue
                
            orig_term = spot["terminal_id"]
            start_h = spot["start_hour"]
            end_h = spot["end_hour"]
            
            # Find candidate vessels
            candidate_vessels = vessels_df[
                (vessels_df["preferred_terminal"] == orig_term) &
                (vessels_df["arrival_time"] >= start_h - 1.0) &
                (vessels_df["arrival_time"] <= end_h)
            ].sort_values("priority", ascending=False)
            
            for _, vessel in candidate_vessels.iterrows():
                v_id = vessel["vessel_id"]
                v_name = vessel["vessel_name"]
                draft = vessel["draft"]
                loa = vessel["length_overall"]
                v_teu = vessel["cargo_volume"]
                arr_time = vessel["arrival_time"]
                
                # Check potential candidate alternative terminals
                alt_terms = [t for t in terminals_df["terminal_id"].unique() if t != orig_term]
                
                best_alt = None
                best_score = float("inf")
                feasible_alts = []

                for alt in alt_terms:
                    limits = term_berth_limits.get(alt, {"max_draft": 0, "max_length": 0, "berth_count": 0})
                    # Check physical compatibility
                    if draft > limits["max_draft"] or loa > limits["max_length"]:
                        continue  # Vessel too large for this terminal
                    
                    # Check destination terminal risk at arrival time
                    alt_hour_row = scored_features_df[
                        (scored_features_df["terminal_id"] == alt) &
                        (scored_features_df["hour"] == int(arr_time))
                    ]
                    alt_risk = float(alt_hour_row["risk_score"].iloc[0]) if len(alt_hour_row) > 0 else 30.0
                    
                    # Check yard headroom
                    alt_meta = terminal_map[alt]
                    yard_util = float(alt_meta["current_yard_utilization"])
                    
                    # Rerouting suitability score (lower is better)
                    suitability = alt_risk * 0.6 + (yard_util * 100) * 0.4
                    
                    if alt_risk < 55.0 and yard_util < 0.85:
                        feasible_alts.append((alt, suitability, alt_risk, yard_util, alt_meta["terminal_name"]))

                if feasible_alts:
                    # Pick lowest congestion alternative
                    feasible_alts.sort(key=lambda x: x[1])
                    target_alt, score, target_risk, target_yard, target_name = feasible_alts[0]
                    
                    # Estimate delay reduction: in congested terminal, wait is ~ 4.0 - 9.0 hrs, in target ~ 0.5 - 1.5 hrs
                    est_orig_wait = round(float(np.clip((spot["peak_risk_score"] / 10.0) * 0.8, 3.5, 10.5)), 1)
                    est_alt_wait = round(float(np.clip((target_risk / 10.0) * 0.3, 0.5, 2.0)), 1)
                    wait_saved = round(est_orig_wait - est_alt_wait, 1)

                    orig_term_name = terminal_map[orig_term]["terminal_name"]

                    reasoning = (
                        f"{orig_term_name} ({orig_term}) is predicted to experience {spot['severity']} congestion "
                        f"(Risk: {spot['peak_risk_score']}/100) between Hours {int(start_h)} and {int(end_h)} due to {spot['primary_root_cause']}. "
                        f"Redirecting {v_name} ({v_id}) to {target_name} ({target_alt}) is physically compatible "
                        f"(Draft: {draft}m <= {term_berth_limits[target_alt]['max_draft']}m, LOA: {loa}m <= {term_berth_limits[target_alt]['max_length']}m) "
                        f"and leverages available yard headroom ({int((1-target_yard)*100)}% free). "
                        f"Estimated turnaround savings: {wait_saved} hours."
                    )

                    recommendations.append({
                        "recommendation_id": f"REC-ROUTE-{v_id}",
                        "vessel_id": v_id,
                        "vessel_name": v_name,
                        "vessel_priority": vessel["priority"],
                        "vessel_size": vessel["vessel_size"],
                        "original_terminal": orig_term,
                        "original_terminal_name": orig_term_name,
                        "recommended_terminal": target_alt,
                        "recommended_terminal_name": target_name,
                        "hotspot_id": spot["hotspot_id"],
                        "estimated_wait_time_original_hrs": est_orig_wait,
                        "estimated_wait_time_rerouted_hrs": est_alt_wait,
                        "estimated_time_savings_hrs": wait_saved,
                        "teu_volume": v_teu,
                        "confidence_score": 0.94,
                        "reasoning": reasoning,
                        "action_status": "RECOMMENDED"
                    })

        # Return unique recommendations per vessel
        unique_recs = {}
        for r in recommendations:
            if r["vessel_id"] not in unique_recs:
                unique_recs[r["vessel_id"]] = r
        return list(unique_recs.values())
