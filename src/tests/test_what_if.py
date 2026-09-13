import pytest
from src.backend.data.loader import PortDataLoader
from src.backend.copilot.scenario_simulator import ScenarioSimulator

@pytest.fixture
def sample_port_data():
    loader = PortDataLoader()
    return loader.load_all_data()

def test_what_if_vessel_delay_simulation(sample_port_data):
    vessels = sample_port_data["vessels"]
    berths = sample_port_data["berths"]
    cranes = sample_port_data["cranes"]
    terminals = sample_port_data["terminals"]

    simulator = ScenarioSimulator()
    target_vessel = vessels.iloc[0]["vessel_id"]
    
    sim_result = simulator.run_simulation(
        base_vessels_df=vessels,
        base_berths_df=berths,
        base_cranes_df=cranes,
        base_terminals_df=terminals,
        delayed_vessel_id=target_vessel,
        delay_hours=5.0,
        offline_crane_ids=["CR-102"],
        cargo_surge_pct=10.0
    )

    assert "plan_df" in sim_result
    assert "kpi_metrics" in sim_result
    assert "hotspots" in sim_result
    
    delayed_row = sim_result["plan_df"][sim_result["plan_df"]["vessel_id"] == target_vessel].iloc[0]
    orig_row = vessels[vessels["vessel_id"] == target_vessel].iloc[0]
    
    # Delayed vessel arrival should be strictly updated
    assert delayed_row["eta_hour"] >= orig_row["arrival_time"] + 4.9
