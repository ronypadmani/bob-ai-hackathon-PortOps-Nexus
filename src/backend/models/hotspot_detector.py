import pandas as pd
import numpy as np
from typing import Dict, List, Any

class HotspotDetector:
    """
    Identifies high-risk temporal bottleneck clusters ('Hotspots') where terminal demand
    exceeds physical berth or crane capacity. Identifies affected vessels and calculates
    projected queuing severity.
    """

    def __init__(self, risk_threshold: float = 50.0):
        self.risk_threshold = risk_threshold

    def detect_hotspots(
        self,
        scored_features_df: pd.DataFrame,
        vessels_df: pd.DataFrame,
        terminals_df: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """
        Scans hourly scored features to group contiguous periods where risk_score >= threshold.
        Returns detailed hotspot descriptions with root-cause diagnostic tags.
        """
        hotspots = []
        terminals = scored_features_df["terminal_id"].unique()

        for term in terminals:
            term_df = scored_features_df[scored_features_df["terminal_id"] == term].sort_values("hour")
            in_hotspot = False
            current_hotspot = None

            for _, row in term_df.iterrows():
                hour = row["hour"]
                score = row["risk_score"]
                is_severe = (score >= self.risk_threshold)

                if is_severe and not in_hotspot:
                    in_hotspot = True
                    current_hotspot = {
                        "terminal_id": term,
                        "start_hour": hour,
                        "end_hour": hour + 1.0,
                        "peak_risk_score": score,
                        "avg_risk_score": score,
                        "scores": [score],
                        "max_berth_pressure": row["berth_pressure_ratio"],
                        "max_yard_util": row["yard_utilization"],
                        "max_crane_pressure": row["crane_pressure_ratio"]
                    }
                elif is_severe and in_hotspot:
                    current_hotspot["end_hour"] = hour + 1.0
                    current_hotspot["peak_risk_score"] = max(current_hotspot["peak_risk_score"], score)
                    current_hotspot["scores"].append(score)
                    current_hotspot["max_berth_pressure"] = max(current_hotspot["max_berth_pressure"], row["berth_pressure_ratio"])
                    current_hotspot["max_yard_util"] = max(current_hotspot["max_yard_util"], row["yard_utilization"])
                    current_hotspot["max_crane_pressure"] = max(current_hotspot["max_crane_pressure"], row["crane_pressure_ratio"])
                elif not is_severe and in_hotspot:
                    in_hotspot = False
                    current_hotspot["avg_risk_score"] = round(float(np.mean(current_hotspot["scores"])), 1)
                    hotspots.append(current_hotspot)
                    current_hotspot = None

            if in_hotspot and current_hotspot:
                current_hotspot["avg_risk_score"] = round(float(np.mean(current_hotspot["scores"])), 1)
                hotspots.append(current_hotspot)

        # Enrich hotspots with affected vessels and root causes
        enriched_hotspots = []
        for idx, spot in enumerate(hotspots):
            term = spot["terminal_id"]
            start_h = spot["start_hour"]
            end_h = spot["end_hour"]
            
            # Find vessels arriving or active in this window
            affected = vessels_df[
                (vessels_df["preferred_terminal"] == term) &
                (vessels_df["arrival_time"] < end_h + 2.0) &
                (vessels_df["arrival_time"] + vessels_df["service_duration"] > start_h - 2.0)
            ]
            
            # Diagnostic primary root cause
            root_causes = []
            if spot["max_berth_pressure"] >= 1.2:
                root_causes.append(f"Berth Overbooking ({int(spot['max_berth_pressure']*100)}% demand)")
            if spot["max_yard_util"] >= 0.88:
                root_causes.append(f"Yard Saturation ({int(spot['max_yard_util']*100)}% util)")
            if spot["max_crane_pressure"] >= 1.1:
                root_causes.append(f"Crane Deficit ({round(spot['max_crane_pressure'], 1)}x demand)")
            if not root_causes:
                root_causes.append("Surge Arrival Concentration")

            severity = "CRITICAL" if spot["peak_risk_score"] >= 75.0 else "HIGH"
            
            enriched_hotspots.append({
                "hotspot_id": f"HS-{term}-{int(start_h):02d}",
                "terminal_id": term,
                "start_hour": start_h,
                "end_hour": end_h,
                "duration_hours": round(end_h - start_h, 1),
                "peak_risk_score": spot["peak_risk_score"],
                "avg_risk_score": spot["avg_risk_score"],
                "severity": severity,
                "primary_root_cause": ", ".join(root_causes),
                "affected_vessel_ids": affected["vessel_id"].tolist(),
                "affected_vessel_names": affected["vessel_name"].tolist(),
                "affected_count": len(affected),
                "total_teu_at_risk": float(affected["cargo_volume"].sum())
            })

        return sorted(enriched_hotspots, key=lambda x: x["peak_risk_score"], reverse=True)
