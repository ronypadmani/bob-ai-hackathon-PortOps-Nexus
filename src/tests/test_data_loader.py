import pytest
import pandas as pd
from pathlib import Path
from src.backend.data.loader import PortDataLoader
from src.backend.data.generator import PortDataGenerator

def test_data_generator():
    generator = PortDataGenerator(seed=42)
    data = generator.generate_all()
    
    assert "vessels" in data
    assert "berths" in data
    assert "cranes" in data
    assert "terminals" in data
    
    assert len(data["vessels"]) >= 30
    assert len(data["berths"]) >= 8
    assert len(data["cranes"]) >= 20
    assert len(data["terminals"]) >= 3

def test_data_loader():
    loader = PortDataLoader()
    data = loader.load_all_data()
    
    vessels = data["vessels"]
    assert isinstance(vessels, pd.DataFrame)
    assert not vessels.empty
    assert "arrival_time" in vessels.columns
    assert "service_duration" in vessels.columns
    assert (vessels["arrival_time"] >= 0).all()
    assert (vessels["service_duration"] > 0).all()

def test_data_loader_missing_columns():
    loader = PortDataLoader()
    with pytest.raises(FileNotFoundError):
        loader.load_vessels(filepath=Path("non_existent_file_path.csv"))
