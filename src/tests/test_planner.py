import pytest
import pandas as pd
from src.backend.data.loader import PortDataLoader
from src.backend.models.features import PortFeatureEngineer
from src.backend.models.congestion_model import CongestionRiskPredictor
from src.backend.models.hotspot_detector import HotspotDetector
from src.backend.optimization.routing import AlternateRoutingEngine
from src.backend.optimization.berth_optimizer import BerthOptimizer
from src.backend.optimization.crane_optimizer import CraneOptimizer
from src.backend.planner.plan_generator import OperationalPlanGenerator
from src.backend.planner.metrics import PortMetricsCalculator

@pytest.fixture
def sample_port_data():
    loader = PortDataLoader()
    return loader.load_all_data()

def test_72h_plan_generation_and_kpis(sample_port_data):
    vessels = sample_port_data["vessels"]
    berths = sample_port_data["berths"]
    cranes = sample_port_data["cranes"]
    terminals = sample_port_data["terminals"]

    eng = PortFeatureEngineer()
    features = eng.extract_terminal_hourly_features(vessels, berths, cranes, terminals)
    predictor = CongestionRiskPredictor()
    scored = predictor.predict_features_dataframe(features)
    detector = HotspotDetector()
    hotspots = detector.detect_hotspots(scored, vessels, terminals)

    routing_engine = AlternateRoutingEngine()
    recs = routing_engine.evaluate_routing_recommendations(vessels, terminals, berths, hotspots, scored)
    reroute_overrides = {r["vessel_id"]: r["recommended_terminal"] for r in recs}

    berth_opt = BerthOptimizer(time_limit_seconds=10)
    berth_res = berth_opt.optimize_berth_allocations(vessels, berths, rerouting_overrides=reroute_overrides)
    crane_opt = CraneOptimizer()
    crane_sched = crane_opt.optimize_crane_assignments(berth_res["schedule"], cranes)

    plan_gen = OperationalPlanGenerator()
    plan_df = plan_gen.generate_72h_plan(crane_sched, recs, scored)

    assert len(plan_df) == len(vessels)
    assert "start_time_hour" in plan_df.columns
    assert "end_time_hour" in plan_df.columns
    assert "cranes_assigned" in plan_df.columns
    assert "routing_status" in plan_df.columns

    metrics_calc = PortMetricsCalculator()
    base_df = metrics_calc.compute_baseline_plan(vessels, berths)
    kpis = metrics_calc.calculate_comparative_kpis(base_df, plan_df, berths)

    assert "baseline" in kpis
    assert "optimized" in kpis
    assert "improvements" in kpis
    # Optimized plan must show improvements or parity vs unoptimized naive FIFO
    assert kpis["optimized"]["avg_waiting_time_hours"] <= kpis["baseline"]["avg_waiting_time_hours"] + 0.5
    assert kpis["improvements"]["total_vessel_hours_saved"] >= 0
