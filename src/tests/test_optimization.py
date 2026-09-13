import pytest
import pandas as pd
from src.backend.data.loader import PortDataLoader
from src.backend.optimization.berth_optimizer import BerthOptimizer
from src.backend.optimization.crane_optimizer import CraneOptimizer
from src.backend.optimization.routing import AlternateRoutingEngine
from src.backend.models.features import PortFeatureEngineer
from src.backend.models.congestion_model import CongestionRiskPredictor
from src.backend.models.hotspot_detector import HotspotDetector

@pytest.fixture
def sample_port_data():
    loader = PortDataLoader()
    return loader.load_all_data()

def test_berth_optimizer_feasibility(sample_port_data):
    vessels = sample_port_data["vessels"]
    berths = sample_port_data["berths"]

    optimizer = BerthOptimizer(time_limit_seconds=15)
    result = optimizer.optimize_berth_allocations(vessels, berths)

    assert result["status"] in ["OPTIMAL", "FEASIBLE"]
    schedule = result["schedule"]
    assert len(schedule) == len(vessels)
    
    # Check that start_time >= arrival_time
    assert (schedule["start_time"] >= schedule["arrival_time"] - 1e-3).all()
    assert (schedule["end_time"] > schedule["start_time"]).all()

    # Check non-overlapping on identical berths
    for berth_id in schedule["assigned_berth"].unique():
        b_sched = schedule[schedule["assigned_berth"] == berth_id].sort_values("start_time")
        for i in range(len(b_sched) - 1):
            curr_end = b_sched.iloc[i]["end_time"]
            next_start = b_sched.iloc[i+1]["start_time"]
            assert next_start >= curr_end - 1e-3, f"Overlap detected on berth {berth_id}"

def test_crane_optimizer(sample_port_data):
    vessels = sample_port_data["vessels"]
    berths = sample_port_data["berths"]
    cranes = sample_port_data["cranes"]

    berth_opt = BerthOptimizer(time_limit_seconds=10)
    berth_res = berth_opt.optimize_berth_allocations(vessels, berths)
    
    crane_opt = CraneOptimizer()
    crane_sched = crane_opt.optimize_crane_assignments(berth_res["schedule"], cranes)

    assert "cranes_allocated" in crane_sched.columns
    assert (crane_sched["cranes_allocated"] >= 2).all()
    assert (crane_sched["cranes_allocated"] <= 5).all()
    assert "optimized_service_duration" in crane_sched.columns
    assert "crane_assignment_reason" in crane_sched.columns

def test_alternate_routing(sample_port_data):
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

    routing_engine = AlternateRoutingEngine(congestion_threshold=40.0)
    recs = routing_engine.evaluate_routing_recommendations(vessels, terminals, berths, hotspots, scored)

    assert isinstance(recs, list)
    if recs:
        r = recs[0]
        assert "vessel_id" in r
        assert "original_terminal" in r
        assert "recommended_terminal" in r
        assert r["original_terminal"] != r["recommended_terminal"]
        assert r["estimated_time_savings_hrs"] > 0
