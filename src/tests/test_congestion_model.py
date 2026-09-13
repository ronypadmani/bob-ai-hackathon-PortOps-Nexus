import pytest
import pandas as pd
from src.backend.data.loader import PortDataLoader
from src.backend.models.features import PortFeatureEngineer
from src.backend.models.congestion_model import CongestionRiskPredictor
from src.backend.models.hotspot_detector import HotspotDetector

@pytest.fixture
def sample_port_data():
    loader = PortDataLoader()
    return loader.load_all_data()

def test_feature_engineering(sample_port_data):
    vessels = sample_port_data["vessels"]
    berths = sample_port_data["berths"]
    cranes = sample_port_data["cranes"]
    terminals = sample_port_data["terminals"]

    engineer = PortFeatureEngineer(horizon_hours=72)
    features_df = engineer.extract_terminal_hourly_features(vessels, berths, cranes, terminals)

    assert not features_df.empty
    assert len(features_df) == 72 * len(terminals["terminal_id"].unique())
    assert "berth_pressure_ratio" in features_df.columns
    assert "yard_utilization" in features_df.columns

def test_congestion_risk_prediction(sample_port_data):
    vessels = sample_port_data["vessels"]
    berths = sample_port_data["berths"]
    cranes = sample_port_data["cranes"]
    terminals = sample_port_data["terminals"]

    engineer = PortFeatureEngineer(horizon_hours=72)
    features_df = engineer.extract_terminal_hourly_features(vessels, berths, cranes, terminals)

    predictor = CongestionRiskPredictor()
    scored_df = predictor.predict_features_dataframe(features_df)

    assert "risk_score" in scored_df.columns
    assert "risk_category" in scored_df.columns
    assert scored_df["risk_score"].min() >= 0.0
    assert scored_df["risk_score"].max() <= 100.0
    assert set(scored_df["risk_category"].unique()).issubset({"LOW", "MEDIUM", "HIGH", "CRITICAL"})

def test_hotspot_detection(sample_port_data):
    vessels = sample_port_data["vessels"]
    berths = sample_port_data["berths"]
    cranes = sample_port_data["cranes"]
    terminals = sample_port_data["terminals"]

    engineer = PortFeatureEngineer(horizon_hours=72)
    features_df = engineer.extract_terminal_hourly_features(vessels, berths, cranes, terminals)
    predictor = CongestionRiskPredictor()
    scored_df = predictor.predict_features_dataframe(features_df)

    detector = HotspotDetector(risk_threshold=45.0)
    hotspots = detector.detect_hotspots(scored_df, vessels, terminals)

    assert isinstance(hotspots, list)
    if hotspots:
        spot = hotspots[0]
        assert "hotspot_id" in spot
        assert "start_hour" in spot
        assert "end_hour" in spot
        assert "primary_root_cause" in spot
        assert "peak_risk_score" in spot
