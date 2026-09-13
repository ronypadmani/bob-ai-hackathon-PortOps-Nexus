from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
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
from src.backend.copilot.scenario_simulator import ScenarioSimulator

app = FastAPI(
    title="IBM Bob Port Operations Copilot API",
    description="REST API for real-time port congestion prediction, Google OR-Tools optimization, and Bob Copilot assistance.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize engines
loader = PortDataLoader()
data = loader.load_all_data()
vessels_df = data["vessels"]
berths_df = data["berths"]
cranes_df = data["cranes"]
terminals_df = data["terminals"]

feature_eng = PortFeatureEngineer()
predictor = CongestionRiskPredictor()
detector = HotspotDetector()
routing_engine = AlternateRoutingEngine()
berth_opt = BerthOptimizer(time_limit_seconds=15)
crane_opt = CraneOptimizer()
plan_gen = OperationalPlanGenerator()
metrics_calc = PortMetricsCalculator()
bob_agent = BobCopilotAgent()
simulator = ScenarioSimulator()

# Run baseline pipeline on startup
features_df = feature_eng.extract_terminal_hourly_features(vessels_df, berths_df, cranes_df, terminals_df)
scored_df = predictor.predict_features_dataframe(features_df)
hotspots = detector.detect_hotspots(scored_df, vessels_df, terminals_df)
routing_recs = routing_engine.evaluate_routing_recommendations(vessels_df, terminals_df, berths_df, hotspots, scored_df)
rerouting_overrides = {r["vessel_id"]: r["recommended_terminal"] for r in routing_recs}
berth_res = berth_opt.optimize_berth_allocations(vessels_df, berths_df, rerouting_overrides=rerouting_overrides)
crane_sched = crane_opt.optimize_crane_assignments(berth_res["schedule"], cranes_df)
plan_df = plan_gen.generate_72h_plan(crane_sched, routing_recs, scored_df)
baseline_df = metrics_calc.compute_baseline_plan(vessels_df, berths_df)
kpi_metrics = metrics_calc.calculate_comparative_kpis(baseline_df, plan_df, berths_df)

class CopilotQueryRequest(BaseModel):
    question: str

class ScenarioSimulateRequest(BaseModel):
    delayed_vessel_id: Optional[str] = None
    delay_hours: float = 0.0
    offline_crane_ids: Optional[List[str]] = None
    cargo_surge_pct: float = 0.0

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "Port Operations Copilot API", "version": "1.0.0"}

@app.get("/api/v1/port/status")
def get_port_status():
    return {
        "total_vessels": len(vessels_df),
        "total_berths": len(berths_df),
        "total_cranes": len(cranes_df),
        "kpi_metrics": kpi_metrics
    }

@app.get("/api/v1/congestion/hotspots")
def get_congestion_hotspots():
    return {"hotspots": hotspots}

@app.get("/api/v1/optimization/schedule")
def get_optimization_schedule():
    return {
        "schedule": plan_df.to_dict(orient="records"),
        "kpi_metrics": kpi_metrics
    }

@app.get("/api/v1/optimization/rerouting")
def get_rerouting_recommendations():
    return {"recommendations": routing_recs}

@app.post("/api/v1/copilot/query")
def ask_copilot(req: CopilotQueryRequest):
    res = bob_agent.query(
        question=req.question,
        plan_df=plan_df,
        hotspots=hotspots,
        routing_recs=routing_recs,
        kpi_metrics=kpi_metrics,
        terminals_df=terminals_df,
        vessels_df=vessels_df
    )
    return res

@app.post("/api/v1/scenario/simulate")
def simulate_scenario(req: ScenarioSimulateRequest):
    sim_result = simulator.run_simulation(
        base_vessels_df=vessels_df,
        base_berths_df=berths_df,
        base_cranes_df=cranes_df,
        base_terminals_df=terminals_df,
        delayed_vessel_id=req.delayed_vessel_id,
        delay_hours=req.delay_hours,
        offline_crane_ids=req.offline_crane_ids,
        cargo_surge_pct=req.cargo_surge_pct
    )
    return {
        "kpi_metrics": sim_result["kpi_metrics"],
        "hotspots_count": len(sim_result["hotspots"]),
        "routing_recommendations_count": len(sim_result["routing_recommendations"]),
        "plan_sample": sim_result["plan_df"].head(10).to_dict(orient="records")
    }
