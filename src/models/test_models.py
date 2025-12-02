import pickle
import numpy as np
from sklearn.metrics import accuracy_score

THRESHOLD = 0.12429071353802519

# ------------------------------
# LOAD SCALER + MODEL
# ------------------------------
import joblib

kmeans = joblib.load("models/kmeans.pkl")
scaler = joblib.load("models/scaler.pkl")


# ------------------------------
# GENERATE SYNTHETIC BORDERLINE FLOWS
# ------------------------------

def generate_flow(shift):
    """
    Tworzy sztuczny flow który daje anomaly score blisko threshold.
    shift = -0.02 → trochę niżej
    shift = 0     → idealnie na threshold
    shift = +0.02 → trochę wyżej
    """

    # Bazowy losowy flow w sensownej skali
    flow = np.array([
        np.random.uniform(0, 2e6),   # duration
        np.random.uniform(1, 30),    # tot_fwd_pkts
        np.random.uniform(1, 30),    # tot_bwd_pkts
        np.random.uniform(0, 6000),  # src_bytes
        np.random.uniform(0, 6000),  # dst_bytes
        np.random.uniform(2, 60),    # total_pkts
        np.random.uniform(50, 12000),# total_bytes
        np.random.choice([6,17,1])   # protocol
    ])

    # Skalowanie
    X = scaler.transform([flow])

    # Obliczamy aktualny anomaly score
    dist = np.min(np.linalg.norm(X - kmeans.cluster_centers_, axis=1))

    # Normalizujemy tak, by flow był blisko threshold
    target_score = THRESHOLD * (1 + shift)
    correction_factor = target_score / (dist + 1e-9)
    X_corrected = X * correction_factor

    # Finalny anomaly score
    final_score = np.min(np.linalg.norm(X_corrected - kmeans.cluster_centers_, axis=1))

    return X_corrected[0], final_score


# ------------------------------
# GENERATE DATASET
# ------------------------------

flows = []
scores = []
true_labels = []  # 0 = normal, 1 = anomaly
pred_labels = []

# 100 flows poniżej threshold
for _ in range(100):
    f, s = generate_flow(-0.05)
    flows.append(f)
    scores.append(s)
    true_labels.append(0)  # powinien być normal

# 100 flows powyżej threshold
for _ in range(100):
    f, s = generate_flow(+0.05)
    flows.append(f)
    scores.append(s)
    true_labels.append(1)  # powinien być anomaly

# 100 flows bardzo blisko threshold
for _ in range(100):
    f, s = generate_flow(0.0)
    flows.append(f)
    scores.append(s)
    # losowo: bo to naprawdę borderline
    true_labels.append(np.random.choice([0, 1]))


# ------------------------------
# MODEL PREDICTION
# ------------------------------
for s in scores:
    pred_labels.append(1 if s > THRESHOLD else 0)

true_labels = np.array(true_labels)
pred_labels = np.array(pred_labels)

# ------------------------------
# ACCURACY
# ------------------------------
accuracy = accuracy_score(true_labels, pred_labels)

print(f"Generated flow count: {len(scores)}")
print(f"Accuracy on borderline synthetic flows: {accuracy * 100:.2f}%")

# Extra insight:
print("\n--- Stats ---")
print(f"Mean score below threshold:  {np.mean(scores[:100]):.5f}")
print(f"Mean score above threshold:  {np.mean(scores[100:200]):.5f}")
print(f"Mean score borderline:       {np.mean(scores[200:300]):.5f}")
