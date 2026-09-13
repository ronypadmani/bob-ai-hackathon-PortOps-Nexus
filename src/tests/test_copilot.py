import pytest
from src.backend.data.loader import PortDataLoader
from src.backend.models.features import PortFeatureEngineer
from src.backend.models.congestion_model import CongestionRiskPredictor
from src.backend.models.hotspot_detector import HotspotDetector
from src.backend.optimization.routing import AlternateRoutingEngine
from src.backend.optimization.berth_optimizer import BerthOptimizer
from src.backend.optimization.crane_optimizer import CraneOptimizer
from src.backend.planner.plan_generator import OperationalPlanGenerator
from src.backend.planner.metrics import PortMetricsCalculator
from src.backend.copilot.bob_agent import BobCopilotAgent

@pytest.fixture
def copilot_env():
    loader = PortDataLoader()
    data = loader.load_all_data()
    vessels = data["vessels"]
    berths = data["berths"]
    cranes = data["cranes"]
    terminals = data["terminals"]

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

    metrics_calc = PortMetricsCalculator()
    base_df = metrics_calc.compute_baseline_plan(vessels, berths)
    kpis = metrics_calc.calculate_comparative_kpis(base_df, plan_df, berths)

    agent = BobCopilotAgent()

    return {
        "agent": agent,
        "plan_df": plan_df,
        "hotspots": hotspots,
        "recs": recs,
        "kpis": kpis,
        "terminals": terminals,
        "vessels": vessels
    }

def test_copilot_congestion_query(copilot_env):
    agent = copilot_env["agent"]
    res = agent.query(
        question="Which terminal is most likely to become congested?",
        plan_df=copilot_env["plan_df"],
        hotspots=copilot_env["hotspots"],
        routing_recs=copilot_env["recs"],
        kpi_metrics=copilot_env["kpis"],
        terminals_df=copilot_env["terminals"],
        vessels_df=copilot_env["vessels"]
    )
    assert "answer" in res
    assert "supporting_data" in res
    assert "reasoning" in res
    assert len(res["answer"]) > 20

def test_copilot_rerouting_query(copilot_env):
    agent = copilot_env["agent"]
    res = agent.query(
        question="Which vessels should be rerouted?",
        plan_df=copilot_env["plan_df"],
        hotspots=copilot_env["hotspots"],
        routing_recs=copilot_env["recs"],
        kpi_metrics=copilot_env["kpis"],
        terminals_df=copilot_env["terminals"],
        vessels_df=copilot_env["vessels"]
    )
    assert "answer" in res
    assert "reroute" in res["answer"].lower() or "vessel" in res["answer"].lower()

def test_copilot_vessel_audit_query(copilot_env):
    agent = copilot_env["agent"]
    v_target = copilot_env["vessels"].iloc[0]["vessel_id"]
    res = agent.query(
        question=f"Why was Vessel {v_target} assigned to its berth?",
        plan_df=copilot_env["plan_df"],
        hotspots=copilot_env["hotspots"],
        routing_recs=copilot_env["recs"],
        kpi_metrics=copilot_env["kpis"],
        terminals_df=copilot_env["terminals"],
        vessels_df=copilot_env["vessels"]
    )
    assert "answer" in res
    assert v_target in res["answer"]
