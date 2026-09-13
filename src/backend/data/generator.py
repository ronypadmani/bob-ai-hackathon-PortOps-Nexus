import os
import random
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Optional

class PortDataGenerator:
    """
    Synthesizes realistic, domain-grounded port operations datasets for vessels, berths, cranes,
    and terminals across a rolling 72-hour planning horizon.
    
    Generates realistic peak arrival surges, capacity bottlenecks, and vessel priority mixes
    modeled after major deepwater container ports (e.g. San Pedro Bay / LA-Long Beach complex).
    """

    def __init__(self, seed: int = 42, horizon_hours: int = 72):
        self.seed = seed
        self.horizon_hours = horizon_hours
        np.random.seed(seed)
        random.seed(seed)

    def generate_all(self, output_dir: Optional[Path] = None) -> Dict[str, pd.DataFrame]:
        terminals_df = self.generate_terminals()
        berths_df = self.generate_berths()
        cranes_df = self.generate_cranes()
        vessels_df = self.generate_vessels()

        if output_dir is not None:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            vessels_df.to_csv(output_dir / "vessels.csv", index=False)
            berths_df.to_csv(output_dir / "berths.csv", index=False)
            cranes_df.to_csv(output_dir / "cranes.csv", index=False)
            terminals_df.to_csv(output_dir / "terminals.csv", index=False)

        return {
            "vessels": vessels_df,
            "berths": berths_df,
            "cranes": cranes_df,
            "terminals": terminals_df
        }

    def generate_terminals(self) -> pd.DataFrame:
        data = [
            {
                "terminal_id": "T1",
                "terminal_name": "Pier 400 Global Gateway",
                "yard_capacity": 90000,
                "current_yard_utilization": 0.78,
                "max_vessels": 4,
                "alternative_terminal": "T2,T3",
                "avg_dwell_time_days": 4.1,
                "rail_connectivity": True
            },
            {
                "terminal_id": "T2",
                "terminal_name": "Pier A Harbor Central",
                "yard_capacity": 65000,
                "current_yard_utilization": 0.91,  # Congested terminal
                "max_vessels": 3,
                "alternative_terminal": "T1,T3",
                "avg_dwell_time_days": 5.8,
                "rail_connectivity": True
            },
            {
                "terminal_id": "T3",
                "terminal_name": "Long Beach Automation Hub",
                "yard_capacity": 80000,
                "current_yard_utilization": 0.54,  # Underutilized high-tech terminal
                "max_vessels": 3,
                "alternative_terminal": "T1,T2",
                "avg_dwell_time_days": 3.2,
                "rail_connectivity": True
            }
        ]
        return pd.DataFrame(data)

    def generate_berths(self) -> pd.DataFrame:
        data = [
            # Terminal 1 Berths (Deep water & Standard)
            {"berth_id": "B101", "terminal_id": "T1", "berth_type": "CONTAINER_DEEP_WATER", "max_length": 420.0, "max_draft": 16.5, "capacity": 1, "available_from": 0.0, "available_until": 72.0, "status": "ACTIVE"},
            {"berth_id": "B102", "terminal_id": "T1", "berth_type": "CONTAINER_DEEP_WATER", "max_length": 400.0, "max_draft": 16.0, "capacity": 1, "available_from": 0.0, "available_until": 72.0, "status": "ACTIVE"},
            {"berth_id": "B103", "terminal_id": "T1", "berth_type": "CONTAINER_STANDARD", "max_length": 350.0, "max_draft": 14.5, "capacity": 1, "available_from": 0.0, "available_until": 72.0, "status": "ACTIVE"},
            {"berth_id": "B104", "terminal_id": "T1", "berth_type": "CONTAINER_STANDARD", "max_length": 320.0, "max_draft": 14.0, "capacity": 1, "available_from": 0.0, "available_until": 72.0, "status": "ACTIVE"},
            
            # Terminal 2 Berths (Oversubscribed)
            {"berth_id": "B201", "terminal_id": "T2", "berth_type": "CONTAINER_DEEP_WATER", "max_length": 380.0, "max_draft": 15.5, "capacity": 1, "available_from": 0.0, "available_until": 72.0, "status": "ACTIVE"},
            {"berth_id": "B202", "terminal_id": "T2", "berth_type": "CONTAINER_STANDARD", "max_length": 340.0, "max_draft": 14.2, "capacity": 1, "available_from": 0.0, "available_until": 72.0, "status": "ACTIVE"},
            {"berth_id": "B203", "terminal_id": "T2", "berth_type": "FEEDER_BERTH", "max_length": 250.0, "max_draft": 12.0, "capacity": 1, "available_from": 0.0, "available_until": 72.0, "status": "ACTIVE"},
            
            # Terminal 3 Berths (Modern High-Capacity)
            {"berth_id": "B301", "terminal_id": "T3", "berth_type": "CONTAINER_DEEP_WATER", "max_length": 440.0, "max_draft": 17.0, "capacity": 1, "available_from": 0.0, "available_until": 72.0, "status": "ACTIVE"},
            {"berth_id": "B302", "terminal_id": "T3", "berth_type": "CONTAINER_DEEP_WATER", "max_length": 400.0, "max_draft": 16.5, "capacity": 1, "available_from": 0.0, "available_until": 72.0, "status": "ACTIVE"},
            {"berth_id": "B303", "terminal_id": "T3", "berth_type": "CONTAINER_STANDARD", "max_length": 360.0, "max_draft": 15.0, "capacity": 1, "available_from": 0.0, "available_until": 72.0, "status": "ACTIVE"},
        ]
        return pd.DataFrame(data)

    def generate_cranes(self) -> pd.DataFrame:
        cranes = []
        # T1 Cranes (12 Cranes)
        for i in range(1, 13):
            berth_target = f"B10{((i - 1) // 3) + 1}"
            cranes.append({
                "crane_id": f"CR-1{i:02d}",
                "terminal_id": "T1",
                "berth_id": berth_target,
                "capacity": 30.0,  # 30 container moves per hour
                "availability": 1.0,
                "available_from": 0.0,
                "available_until": 72.0,
                "status": "OPERATIONAL"
            })
            
        # T2 Cranes (8 Cranes, Crane CR-204 scheduled maintenance at H20-H32)
        for i in range(1, 9):
            berth_target = f"B20{min(3, ((i - 1) // 3) + 1)}"
            status = "MAINTENANCE" if i == 4 else "OPERATIONAL"
            avail = 0.5 if i == 4 else 1.0
            cranes.append({
                "crane_id": f"CR-2{i:02d}",
                "terminal_id": "T2",
                "berth_id": berth_target,
                "capacity": 27.0,
                "availability": avail,
                "available_from": 0.0,
                "available_until": 72.0,
                "status": status
            })

        # T3 Cranes (10 Automated Cranes, higher productivity)
        for i in range(1, 11):
            berth_target = f"B30{min(3, ((i - 1) // 4) + 1)}"
            cranes.append({
                "crane_id": f"CR-3{i:02d}",
                "terminal_id": "T3",
                "berth_id": berth_target,
                "capacity": 35.0,  # Automated fast moves
                "availability": 1.0,
                "available_from": 0.0,
                "available_until": 72.0,
                "status": "OPERATIONAL"
            })
            
        return pd.DataFrame(cranes)

    def generate_vessels(self) -> pd.DataFrame:
        vessel_names = [
            "Ever Forward", "Maersk Mc-Kinney", "CMA CGM Palais", "MSC Isabella", "OOCL Hong Kong",
            "COSCO Shipping Universe", "Hapag-Lloyd Al Jmeliyah", "ONE Integrity", "Yang Ming Wellhead", "HMM Algeciras",
            "Pacific Voyager", "Ever Golden", "Madrid Maersk", "MSC Gulsun", "CMA CGM Rivoli",
            "APL Fullerton", "ZIM Antwerp", "Wan Hai 805", "Hyundai Singapore", "Ever Fortune",
            "Munich Maersk", "MSC Oscar", "CMA CGM Tenere", "COSCO Faith", "ONE Apus",
            "Ever Given", "HMM Dublin", "Maersk Honam", "MSC Zoe", "OOCL Germany",
            "CMA CGM Jacques Saade", "MSC Mina", "COSCO Galaxy", "ONE Triumph", "Hapag-Lloyd Berlin Express",
            "ZIM Kingston", "APL Southampton", "Ever Ace", "MSC Samar", "Maersk Eindhoven"
        ]

        vessel_classes = {
            "ULCV": {"length": 400.0, "draft": 16.0, "moves_range": (2800, 3800), "teu": (16000, 24000), "weight": 0.25},
            "POST_PANAMAX": {"length": 350.0, "draft": 14.5, "moves_range": (1800, 2600), "teu": (9000, 15000), "weight": 0.35},
            "PANAMAX": {"length": 294.0, "draft": 13.0, "moves_range": (1100, 1700), "teu": (4500, 8500), "weight": 0.25},
            "FEEDER": {"length": 210.0, "draft": 10.5, "moves_range": (600, 1000), "teu": (1500, 3500), "weight": 0.15},
        }
        
        priorities = ["CRITICAL", "HIGH", "NORMAL", "LOW"]
        priority_weights = [0.12, 0.28, 0.45, 0.15]
        
        destinations = ["Inland Intermodal Rail", "Local Metro DC", "Transshipment Hub", "Automotive Assembly Line"]
        
        records = []
        
        # Staggered arrivals with a major surge cluster at Terminal T2 between Hours 12 and 30
        arrival_times = []
        # Base spread across 72 hours
        for i in range(len(vessel_names)):
            if i < 12:
                # Early shift (Hours 0 - 18)
                arr = np.random.uniform(1.0, 16.0)
            elif i < 26:
                # Surge window (Hours 12 - 32)
                arr = np.random.uniform(14.0, 32.0)
            elif i < 35:
                # Mid-horizon (Hours 32 - 54)
                arr = np.random.uniform(32.0, 54.0)
            else:
                # Late-horizon (Hours 54 - 68)
                arr = np.random.uniform(54.0, 68.0)
            arrival_times.append(round(float(arr), 1))
            
        arrival_times.sort()

        for idx, name in enumerate(vessel_names):
            v_id = f"V{101 + idx}"
            v_type = np.random.choice(list(vessel_classes.keys()), p=[v["weight"] for v in vessel_classes.values()])
            meta = vessel_classes[v_type]
            
            containers = int(np.random.randint(meta["moves_range"][0], meta["moves_range"][1]))
            cargo_teu = int(np.random.randint(meta["teu"][0], meta["teu"][1]))
            arr_time = arrival_times[idx]
            
            # Skew terminal preference: create hotspot at T2 for mid-window arrivals
            if 14.0 <= arr_time <= 32.0 and np.random.random() < 0.65:
                pref_term = "T2"
            else:
                pref_term = np.random.choice(["T1", "T2", "T3"], p=[0.40, 0.35, 0.25])

            priority = np.random.choice(priorities, p=priority_weights)
            
            # Base service duration using standard 3 cranes @ 28 moves/hr
            # duration = containers / (3 * 28) = containers / 84
            base_duration = round(containers / 84.0, 1)
            est_dep = round(arr_time + base_duration + 2.0, 1)

            records.append({
                "vessel_id": v_id,
                "vessel_name": name,
                "arrival_time": arr_time,
                "estimated_departure": est_dep,
                "cargo_volume": float(cargo_teu),
                "containers": containers,
                "vessel_size": v_type,
                "draft": meta["draft"],
                "length_overall": meta["length"],
                "preferred_terminal": pref_term,
                "priority": priority,
                "destination": np.random.choice(destinations),
                "service_duration": base_duration
            })

        return pd.DataFrame(records).sort_values("arrival_time").reset_index(drop=True)

if __name__ == "__main__":
    generator = PortDataGenerator()
    data_dir = Path(__file__).resolve().parent / "sample_data"
    generator.generate_all(data_dir)
    print(f"Generated realistic sample data in {data_dir}")
