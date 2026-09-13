import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from ..data.loader import PortDataLoader
from ..models.features import PortFeatureEngineer
from ..models.congestion_model import CongestionRiskPredictor
from ..models.hotspot_detector import HotspotDetector
from ..optimization.routing import AlternateRoutingEngine
from ..optimization.berth_optimizer import BerthOptimizer
from ..optimization.crane_optimizer import CraneOptimizer
from ..planner.plan_generator import OperationalPlanGenerator
from ..planner.metrics import PortMetricsCalculator

class ScenarioSimulator:
    """
    Simulates operational disruptions and What-If scenarios in real-time.
    Recalculates congestion forecasts, OR-Tools berth/crane allocations, and comparative impact deltas.
    """

    def __init__(self):
        self.feature_eng = PortFeatureEngineer()
        self.predictor = CongestionRiskPredictor()
        self.detector = HotspotDetector()
        self.routing_engine = AlternateRoutingEngine()
        self.berth_opt = BerthOptimizer(time_limit_seconds=15)
        self.crane_opt = CraneOptimizer()
        self.plan_gen = OperationalPlanGenerator()
        self.metrics_calc = PortMetricsCalculator()

    def run_simulation(
        self,
        base_vessels_df: pd.DataFrame,
        base_berths_df: pd.DataFrame,
        base_cranes_df: pd.DataFrame,
        base_terminals_df: pd.DataFrame,
        delayed_vessel_id: Optional[str] = None,
        delay_hours: float = 0.0,
        offline_crane_ids: Optional[List[str]] = None,
        cargo_surge_pct: float = 0.0,
        weather_slowdown_window: Optional[tuple] = None  # (start_h, end_h, slowdown_factor)
    ) -> Dict[str, Any]:
        """
        Executes end-to-end recalculated pipeline with simulated perturbations.
        """
        vessels = base_vessels_df.copy()
        berths = base_berths_df.copy()
        cranes = base_cranes_df.copy()
        terminals = base_terminals_df.copy()

        # Apply vessel delay
        if delayed_vessel_id and delay_hours != 0.0:
            mask = vessels["vessel_id"] == delayed_vessel_id
            if mask.any():
                vessels.loc[mask, "arrival_time"] = vessels.loc[mask, "arrival_time"] + delay_hours
                vessels.loc[mask, "estimated_departure"] = vessels.loc[mask, "estimated_departure"] + delay_hours
                vessels = vessels.sort_values("arrival_time").reset_index(drop=True)

        # Apply crane outages
        if offline_crane_ids:
            cranes.loc[cranes["crane_id"].isin(offline_crane_ids), "status"] = "MAINTENANCE"
            cranes.loc[cranes["crane_id"].isin(offline_crane_ids), "availability"] = 0.0

        # Apply cargo surge
        if cargo_surge_pct > 0.0:
            vessels["containers"] = (vessels["containers"] * (1.0 + cargo_surge_pct / 100.0)).astype(int)
            vessels["cargo_volume"] = vessels["cargo_volume"] * (1.0 + cargo_surge_pct / 100.0)
            vessels["service_duration"] = (vessels["containers"] / 84.0).round(1)

        # Apply weather slowdown
        if weather_slowdown_window:
            w_start, w_end, factor = weather_slowdown_window
            # Vessels arriving in window take longer
            w_mask = (vessels["arrival_time"] >= w_start) & (vessels["arrival_time"] <= w_end)
            vessels.loc[w_mask, "service_duration"] = vessels.loc[w_mask, "service_duration"] * factor

        # 1. Feature Engineering & Congestion Risk
        features_df = self.feature_eng.extract_terminal_hourly_features(vessels, berths, cranes, terminals)
        scored_df = self.predictor.predict_features_dataframe(features_df)
        
        # 2. Hotspots & Rerouting
        hotspots = self.detector.detect_hotspots(scored_df, vessels, terminals)
        routing_recs = self.routing_engine.evaluate_routing_recommendations(
            vessels, terminals, berths, hotspots, scored_df
        )

        rerouting_overrides = {r["vessel_id"]: r["recommended_terminal"] for r in routing_recs}

        # 3. OR-Tools Berth Optimization
        berth_result = self.berth_opt.optimize_berth_allocations(
            vessels, berths, rerouting_overrides=rerouting_overrides
        )
        schedule_df = berth_result["schedule"]

        # 4. Crane Allocation Optimization
        crane_schedule_df = self.crane_opt.optimize_crane_assignments(schedule_df, cranes)

        # 5. 72-Hour Plan Generation
        plan_df = self.plan_gen.generate_72h_plan(crane_schedule_df, routing_recs, scored_df)

        # 6. Baseline vs Optimized KPIs
        baseline_df = self.metrics_calc.compute_baseline_plan(vessels, berths)
        kpi_metrics = self.metrics_calc.calculate_comparative_kpis(baseline_df, plan_df, berths)

        return {
            "vessels": vessels,
            "berths": berths,
            "cranes": cranes,
            "terminals": terminals,
            "scored_features": scored_df,
            "hotspots": hotspots,
            "routing_recommendations": routing_recs,
            "berth_result": berth_result,
            "crane_schedule": crane_schedule_df,
            "plan_df": plan_df,
            "kpi_metrics": kpi_metrics
        }
