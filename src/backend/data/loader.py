import os
import pandas as pd
from pathlib import Path
from typing import Dict, Tuple, Optional
from pydantic import BaseModel, Field

class VesselRecord(BaseModel):
    vessel_id: str
    vessel_name: str
    arrival_time: float = Field(ge=0.0)
    estimated_departure: float = Field(ge=0.0)
    cargo_volume: float = Field(ge=0.0)
    containers: int = Field(ge=0)
    vessel_size: str
    draft: float = Field(ge=0.0)
    length_overall: float = Field(ge=0.0)
    preferred_terminal: str
    priority: str
    destination: str
    service_duration: float = Field(ge=1.0)

class BerthRecord(BaseModel):
    berth_id: str
    terminal_id: str
    berth_type: str
    max_length: float = Field(ge=50.0)
    max_draft: float = Field(ge=5.0)
    capacity: int = Field(ge=1)
    available_from: float = Field(ge=0.0)
    available_until: float = Field(ge=0.0)
    status: str

class CraneRecord(BaseModel):
    crane_id: str
    terminal_id: str
    berth_id: str
    capacity: float = Field(ge=10.0)  # moves per hour
    availability: float = Field(ge=0.0, le=1.0)
    available_from: float = Field(ge=0.0)
    available_until: float = Field(ge=0.0)
    status: str

class TerminalRecord(BaseModel):
    terminal_id: str
    terminal_name: str
    yard_capacity: int = Field(ge=1000)
    current_yard_utilization: float = Field(ge=0.0, le=1.0)
    max_vessels: int = Field(ge=1)
    alternative_terminal: str
    rail_connectivity: bool = True

class PortDataLoader:
    """
    Ingests and validates raw CSV datasets for vessels, berths, cranes, and terminals.
    Ensures structural integrity and data quality before feeding the ML and optimization engines.
    """
    
    def __init__(self, data_dir: Optional[Path] = None):
        if data_dir is None:
            self.data_dir = Path(__file__).resolve().parent / "sample_data"
        else:
            self.data_dir = Path(data_dir)
            
    def load_all_data(self) -> Dict[str, pd.DataFrame]:
        """
        Loads all core data tables from CSV and validates records.
        """
        vessels_df = self.load_vessels()
        berths_df = self.load_berths()
        cranes_df = self.load_cranes()
        terminals_df = self.load_terminals()
        
        return {
            "vessels": vessels_df,
            "berths": berths_df,
            "cranes": cranes_df,
            "terminals": terminals_df
        }

    def load_vessels(self, filepath: Optional[Path] = None) -> pd.DataFrame:
        path = filepath or (self.data_dir / "vessels.csv")
        if not path.exists():
            raise FileNotFoundError(f"Vessel dataset not found at {path}")
        df = pd.read_csv(path)
        
        # Validation checks
        required_cols = [
            "vessel_id", "vessel_name", "arrival_time", "estimated_departure",
            "cargo_volume", "containers", "vessel_size", "preferred_terminal",
            "priority", "destination", "service_duration"
        ]
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            raise ValueError(f"vessels.csv missing required columns: {missing}")
            
        df["arrival_time"] = df["arrival_time"].astype(float)
        df["service_duration"] = df["service_duration"].astype(float)
        df["containers"] = df["containers"].astype(int)
        df["cargo_volume"] = df["cargo_volume"].astype(float)
        
        if "draft" not in df.columns:
            df["draft"] = 14.0
        if "length_overall" not in df.columns:
            df["length_overall"] = 350.0
            
        return df.sort_values(by="arrival_time").reset_index(drop=True)

    def load_berths(self, filepath: Optional[Path] = None) -> pd.DataFrame:
        path = filepath or (self.data_dir / "berths.csv")
        if not path.exists():
            raise FileNotFoundError(f"Berth dataset not found at {path}")
        df = pd.read_csv(path)
        required_cols = ["berth_id", "terminal_id", "berth_type", "capacity", "available_from", "available_until", "status"]
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            raise ValueError(f"berths.csv missing required columns: {missing}")
            
        if "max_length" not in df.columns:
            df["max_length"] = 400.0
        if "max_draft" not in df.columns:
            df["max_draft"] = 16.0
            
        return df.reset_index(drop=True)

    def load_cranes(self, filepath: Optional[Path] = None) -> pd.DataFrame:
        path = filepath or (self.data_dir / "cranes.csv")
        if not path.exists():
            raise FileNotFoundError(f"Crane dataset not found at {path}")
        df = pd.read_csv(path)
        required_cols = ["crane_id", "terminal_id", "capacity", "availability", "status"]
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            raise ValueError(f"cranes.csv missing required columns: {missing}")
            
        if "berth_id" not in df.columns:
            df["berth_id"] = "ALL"
        if "available_from" not in df.columns:
            df["available_from"] = 0.0
        if "available_until" not in df.columns:
            df["available_until"] = 72.0
            
        return df.reset_index(drop=True)

    def load_terminals(self, filepath: Optional[Path] = None) -> pd.DataFrame:
        path = filepath or (self.data_dir / "terminals.csv")
        if not path.exists():
            raise FileNotFoundError(f"Terminal dataset not found at {path}")
        df = pd.read_csv(path)
        required_cols = ["terminal_id", "yard_capacity", "current_yard_utilization", "max_vessels", "alternative_terminal"]
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            raise ValueError(f"terminals.csv missing required columns: {missing}")
            
        if "terminal_name" not in df.columns:
            df["terminal_name"] = df["terminal_id"].apply(lambda x: f"Terminal {x}")
        if "rail_connectivity" not in df.columns:
            df["rail_connectivity"] = True
            
        return df.reset_index(drop=True)
