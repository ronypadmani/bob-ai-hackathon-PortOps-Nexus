import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler

class CongestionRiskPredictor:
    """
    Predicts port congestion risk scores (0-100) and classifications (LOW, MEDIUM, HIGH, CRITICAL)
    using trained ensemble ML models and formulaic domain risk aggregators.
    """

    def __init__(self):
        self.classifier = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
        self.regressor = GradientBoostingRegressor(n_estimators=80, max_depth=4, random_state=42)
        self.scaler = StandardScaler()
        self.feature_cols = [
            "num_arriving", "active_vessels_count", "crit_vessels",
            "total_workload_moves", "available_berths", "total_crane_rate",
            "berth_pressure_ratio", "crane_pressure_ratio", "yard_utilization"
        ]
        self._is_fitted = False
        self._bootstrap_training()

    def _bootstrap_training(self):
        """
        Fits the ML models on a simulated domain dataset of port operational conditions.
        """
        # Generate synthetic training grid (2000 operational states)
        np.random.seed(42)
        n_samples = 2000
        
        arriving = np.random.poisson(lam=1.5, size=n_samples)
        active = np.clip(arriving + np.random.poisson(lam=1.8, size=n_samples), 0, 8)
        crit = np.clip(np.random.binomial(n=active, p=0.35), 0, active)
        workload = active * np.random.uniform(1200, 3000, size=n_samples)
        berths = np.random.choice([3, 4, 5], size=n_samples)
        crane_rate = berths * np.random.uniform(60, 100, size=n_samples)
        
        berth_pressure = active / berths
        crane_pressure = (workload / np.maximum(1, active * 12)) / np.maximum(1.0, crane_rate)
        yard_util = np.clip(np.random.beta(a=5, b=2, size=n_samples) * 0.4 + (active / 8.0) * 0.5, 0.3, 0.98)
        
        # Ground truth continuous risk score (0-100)
        risk_raw = (
            berth_pressure * 35.0 +
            np.clip(crane_pressure, 0, 3) * 15.0 +
            (yard_util ** 2) * 35.0 +
            (crit / np.maximum(1, active)) * 15.0
        )
        risk_scores = np.clip(risk_raw, 0, 100)
        labels = (risk_scores >= 65.0).astype(int)

        X = np.column_stack([
            arriving, active, crit, workload, berths, crane_rate,
            berth_pressure, crane_pressure, yard_util
        ])
        
        X_scaled = self.scaler.fit_transform(X)
        self.classifier.fit(X_scaled, labels)
        self.regressor.fit(X_scaled, risk_scores)
        self._is_fitted = True

    def predict_terminal_risk(self, feature_row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Computes risk score and severity for a single terminal time-window state.
        """
        x_vec = np.array([[feature_row[col] for col in self.feature_cols]])
        x_scaled = self.scaler.transform(x_vec)
        
        ml_score = float(self.regressor.predict(x_scaled)[0])
        ml_prob = float(self.classifier.predict_proba(x_scaled)[0][1])

        # Heuristic ground-truth formula verification
        berth_ratio = feature_row.get("berth_pressure_ratio", 0.0)
        yard_util = feature_row.get("yard_utilization", 0.5)
        crane_ratio = feature_row.get("crane_pressure_ratio", 0.0)
        crit_vessels = feature_row.get("crit_vessels", 0)

        # Domain composite formula
        formula_score = (
            min(40.0, berth_ratio * 30.0) +
            min(30.0, (yard_util ** 1.8) * 32.0) +
            min(20.0, crane_ratio * 15.0) +
            min(10.0, crit_vessels * 4.0)
        )
        
        # Blended calibrated risk score (0 - 100)
        final_score = round(float(np.clip(0.6 * ml_score + 0.4 * formula_score, 0.0, 100.0)), 1)
        
        # Categorization
        if final_score >= 75.0:
            category = "CRITICAL"
        elif final_score >= 50.0:
            category = "HIGH"
        elif final_score >= 25.0:
            category = "MEDIUM"
        else:
            category = "LOW"

        return {
            "risk_score": final_score,
            "risk_category": category,
            "congestion_probability": round(ml_prob, 3),
            "berth_contribution": round(min(40.0, berth_ratio * 30.0), 1),
            "yard_contribution": round(min(30.0, (yard_util ** 1.8) * 32.0), 1),
            "crane_contribution": round(min(20.0, crane_ratio * 15.0), 1),
            "priority_contribution": round(min(10.0, crit_vessels * 4.0), 1),
        }

    def predict_features_dataframe(self, features_df: pd.DataFrame) -> pd.DataFrame:
        """
        Applies prediction over the entire extracted features dataframe.
        """
        df = features_df.copy()
        X = df[self.feature_cols].values
        X_scaled = self.scaler.transform(X)
        
        ml_scores = self.regressor.predict(X_scaled)
        ml_probs = self.classifier.predict_proba(X_scaled)[:, 1]
        
        risk_scores = []
        categories = []
        
        for idx, row in df.iterrows():
            berth_ratio = row["berth_pressure_ratio"]
            yard_util = row["yard_utilization"]
            crane_ratio = row["crane_pressure_ratio"]
            crit_vessels = row["crit_vessels"]
            
            formula_score = (
                min(40.0, berth_ratio * 30.0) +
                min(30.0, (yard_util ** 1.8) * 32.0) +
                min(20.0, crane_ratio * 15.0) +
                min(10.0, crit_vessels * 4.0)
            )
            score = round(float(np.clip(0.6 * ml_scores[idx] + 0.4 * formula_score, 0.0, 100.0)), 1)
            risk_scores.append(score)
            
            if score >= 75.0:
                cat = "CRITICAL"
            elif score >= 50.0:
                cat = "HIGH"
            elif score >= 25.0:
                cat = "MEDIUM"
            else:
                cat = "LOW"
            categories.append(cat)
            
        df["risk_score"] = risk_scores
        df["risk_category"] = categories
        df["congestion_probability"] = [round(float(p), 3) for p in ml_probs]
        
        return df
