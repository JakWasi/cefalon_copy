import os
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import joblib
import matplotlib.pyplot as plt

from sklearn.preprocessing import StandardScaler
from sklearn.cluster import MiniBatchKMeans
from tqdm import tqdm


# ============================================================
# CONFIG
# ============================================================

PARQUET_FILE = "data/flows/processed/merged_dataset.parquet"
MODELS_DIR = "models"
PLOTS_DIR = "models/plots"

BATCH_SIZE = 200_000
N_CLUSTERS = 30
THRESHOLD_PERCENTILE = 98


# ============================================================
# UTILS
# ============================================================

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def load_batches(parquet_path, batch_size):
    table = pq.read_table(parquet_path)
    df = table.to_pandas(split_blocks=True, self_destruct=True)

    for start in range(0, len(df), batch_size):
        yield df.iloc[start:start + batch_size]


def anomaly_score(X_scaled, kmeans):
    labels = kmeans.predict(X_scaled)
    centers = kmeans.cluster_centers_
    return np.linalg.norm(X_scaled - centers[labels], axis=1)


# ============================================================
# MAIN TRAINING PIPELINE
# ============================================================

def main():

    ensure_dir(MODELS_DIR)
    ensure_dir(PLOTS_DIR)

    # =====================================================================
    # 1️⃣ TRAIN SCALER
    # =====================================================================
    print("\n============================================")
    print("  TRAINING StandardScaler")
    print("============================================\n")

    scaler = StandardScaler()

    for batch in tqdm(load_batches(PARQUET_FILE, BATCH_SIZE), desc="Scaler"):
        X = batch.drop(columns=["label"]).values
        scaler.partial_fit(X)

    print("Scaler trained.\n")

    # =====================================================================
    # 2️⃣ TRAIN MiniBatchKMeans
    # =====================================================================

    print("\n============================================")
    print("  TRAINING MiniBatchKMeans")
    print("============================================\n")

    kmeans = MiniBatchKMeans(
        n_clusters=N_CLUSTERS,
        batch_size=5000,
        random_state=42
    )

    batch_rejection_rates = []

    for batch in tqdm(load_batches(PARQUET_FILE, BATCH_SIZE), desc="KMeans"):
        X = batch.drop(columns=["label"]).values
        X_scaled = scaler.transform(X)
        kmeans.partial_fit(X_scaled)

        # optional: track how "strange" batches look
        dists = anomaly_score(X_scaled, kmeans)
        per = np.percentile(dists, THRESHOLD_PERCENTILE)
        batch_rejection_rates.append(per)

    print("KMeans trained.\n")

    # =====================================================================
    # 3️⃣ COMPUTE GLOBAL THRESHOLD
    # =====================================================================

    print("\n============================================")
    print("  COMPUTING THRESHOLD")
    print("============================================\n")

    all_scores = []

    for batch in tqdm(load_batches(PARQUET_FILE, BATCH_SIZE), desc="Scores"):
        X = batch.drop(columns=["label"]).values
        X_scaled = scaler.transform(X)
        d = anomaly_score(X_scaled, kmeans)
        all_scores.append(d)

    all_scores = np.concatenate(all_scores)
    threshold = np.percentile(all_scores, THRESHOLD_PERCENTILE)

    print(f"Threshold computed: {threshold}\n")

    # =====================================================================
    # 4️⃣ SAVE MODELS
    # =====================================================================

    joblib.dump(scaler, f"{MODELS_DIR}/scaler.pkl")
    joblib.dump(kmeans, f"{MODELS_DIR}/kmeans.pkl")
    joblib.dump(threshold, f"{MODELS_DIR}/threshold.pkl")

    print("Models saved.\n")

    # =====================================================================
    # 5️⃣ GENERATE PLOTS
    # =====================================================================
    print("\n============================================")
    print("  GENERATING PLOTS")
    print("============================================\n")

    # Histogram anomaly scores
    plt.figure(figsize=(12, 6))
    plt.hist(all_scores, bins=200, alpha=0.7)
    plt.axvline(threshold, color="red", linestyle="--", label=f"Threshold={threshold:.4f}")
    plt.title("Histogram of Anomaly Scores")
    plt.xlabel("Distance to Nearest Cluster Center")
    plt.ylabel("Count")
    plt.legend()
    plt.grid(True)
    plt.savefig(f"{PLOTS_DIR}/histogram_scores.png")
    plt.close()

    # Histogram in log scale
    plt.figure(figsize=(12, 6))
    plt.hist(all_scores, bins=200, alpha=0.7, log=True)
    plt.axvline(threshold, color="red", linestyle="--", label=f"Threshold={threshold:.4f}")
    plt.title("Histogram of Anomaly Scores (log scale)")
    plt.xlabel("Distance to Nearest Cluster Center")
    plt.ylabel("Count (log)")
    plt.legend()
    plt.grid(True)
    plt.savefig(f"{PLOTS_DIR}/histogram_scores_log.png")
    plt.close()

    # Rejection percent per batch
    plt.figure(figsize=(12, 6))
    plt.plot(batch_rejection_rates, marker='o')
    plt.title(f"Batch {THRESHOLD_PERCENTILE}th Percentile of Anomaly Score per Batch")
    plt.xlabel("Batch idx")
    plt.ylabel("Percentile value")
    plt.grid(True)
    plt.savefig(f"{PLOTS_DIR}/batch_percentile_curve.png")
    plt.close()

    # Cluster center norms
    center_norms = np.linalg.norm(kmeans.cluster_centers_, axis=1)
    plt.figure(figsize=(10, 5))
    plt.bar(range(N_CLUSTERS), center_norms)
    plt.title("Cluster Center Norms")
    plt.xlabel("Cluster ID")
    plt.ylabel("L2 Norm")
    plt.grid(True)
    plt.savefig(f"{PLOTS_DIR}/cluster_center_norms.png")
    plt.close()

    print("All plots saved.")
    print(f"Plots directory: {PLOTS_DIR}\n")

    print("============================================")
    print(" TRAINING + PLOTS DONE 🎉")
    print("============================================")


if __name__ == "__main__":
    main()
