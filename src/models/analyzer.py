# src/models/analyzer.py
import os
import joblib
import numpy as np
import pandas as pd

# Feature order MUST match training
FEATURES = [
    "duration",
    "tot_fwd_pkts",
    "tot_bwd_pkts",
    "src_bytes",
    "dst_bytes",
    "total_pkts",
    "total_bytes",
    "protocol"
]

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "models")

_current_dir = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(_current_dir, "..", ".."))
SCALER_PATH = os.path.join(PROJECT_ROOT, "models", "scaler.pkl")
KMEANS_PATH = os.path.join(PROJECT_ROOT, "models", "kmeans.pkl")
THRESHOLD_PATH = os.path.join(PROJECT_ROOT, "models", "threshold.pkl")


class Analyzer:
    def __init__(self):
        if not os.path.exists(SCALER_PATH) or not os.path.exists(KMEANS_PATH) or not os.path.exists(THRESHOLD_PATH):
            raise FileNotFoundError("Scaler / KMeans / threshold pkl not found under models/. "
                                    "Expected: scaler.pkl, kmeans.pkl, threshold.pkl")
        self.scaler = joblib.load(SCALER_PATH)
        self.kmeans = joblib.load(KMEANS_PATH)
        self.threshold = float(joblib.load(THRESHOLD_PATH))
    def _flow_to_vector(self, flow_row) -> np.ndarray:
        vals = []
        for f in FEATURES:
            if f not in flow_row:
                vals.append(0.0)
            else:
                vals.append(float(flow_row[f]))
        return np.array(vals, dtype=float).reshape(1, -1)
    def score(self, flow_row) -> float:
        x = self._flow_to_vector(flow_row)
        x_scaled = self.scaler.transform(x)
        labels = self.kmeans.predict(x_scaled)
        centers = self.kmeans.cluster_centers_
        dists = np.linalg.norm(x_scaled - centers[labels], axis=1)
        return float(dists[0])
    def label_from_score(self, score: float) -> str:
        if score > self.threshold * 1.8:
            return "attack"
        elif score > self.threshold:
            return "suspicious"
        else:
            return "benign"
    def annotate_df(self, df):
        import numpy as np
        scores = []
        labels = []
        for _, row in df.iterrows():
            sc = self.score(row)
            lb = self.label_from_score(sc)
            scores.append(sc)
            labels.append(lb)
        out = df.copy()
        out["anomaly_score"] = np.array(scores)
        out["label"] = labels
        return out
