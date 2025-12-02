# src/capture/capture_live.py
#!/usr/bin/env python3

import os
import sys
import time
import csv
import socket
from datetime import datetime

# --- FIX PYTHONPATH FOR ANY EXECUTION LOCATION ---
CURRENT = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT, "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
# --------------------------------------------------

from src.control.decision_controller import DecisionController
from src.ingestion.flow_aggregator import FlowAggregator
from src.models.analyzer import Analyzer

try:
    from scapy.all import sniff, IP, TCP, UDP
except Exception as e:
    raise RuntimeError("scapy is required for live capture. Install scapy and run as root.") from e

try:
    import netifaces
except Exception:
    netifaces = None

OUTPUT_FILE = os.path.join(PROJECT_ROOT, "data", "flows", "processed", "live_flows.csv")
FLOW_TIMEOUT = 10.0

# Dodajemy 'timestamp' na pierwszym miejscu
FEATURES = [
    "timestamp",
    "duration",
    "tot_fwd_pkts",
    "tot_bwd_pkts",
    "src_bytes",
    "dst_bytes",
    "total_pkts",
    "total_bytes",
    "protocol",
    "src_ip",
    "dst_ip",
    "src_port",
    "dst_port",
    "anomaly_score",
    "label"
]

import psutil

def detect_interface():
    stats = psutil.net_io_counters(pernic=True)
    best_iface = None
    max_bytes = 0
    for iface, data in stats.items():
        if iface == "lo":
            continue
        total = data.bytes_sent + data.bytes_recv
        if total > max_bytes:
            max_bytes = total
            best_iface = iface
    if best_iface is None:
        for iface in stats:
            if iface != "lo":
                best_iface = iface
                break
    return best_iface or "eth0"

def get_local_ips():
    local_ips = set()
    try:
        for iface in socket.getaddrinfo(socket.gethostname(), None):
            local_ips.add(iface[4][0])
    except:
        pass
    local_ips.add("127.0.0.1")
    return local_ips

def ensure_out():
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    if not os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(FEATURES)

def pkt_to_tuple(pkt):
    if not pkt.haslayer(IP):
        return None
    ip = pkt[IP]
    src = ip.src
    dst = ip.dst
    proto = None
    sport = None
    dport = None
    if pkt.haslayer(TCP):
        proto = 6
        sport = pkt[TCP].sport
        dport = pkt[TCP].dport
    elif pkt.haslayer(UDP):
        proto = 17
        sport = pkt[UDP].sport
        dport = pkt[UDP].dport
    else:
        return None
    size = len(pkt)
    return src, dst, sport, dport, proto, size

def main():
    iface = detect_interface()
    print(f"[capture_live] using interface: {iface}")
    ensure_out()
    local_ips = get_local_ips()
    aggregator = FlowAggregator(timeout=FLOW_TIMEOUT)

    try:
        analyzer = Analyzer()
    except Exception as e:
        print("[capture_live] Analyzer not available:", e)
        analyzer = None

    controller = DecisionController()

    def handle(pkt):
        tup = pkt_to_tuple(pkt)
        if tup is None:
            return
        src, dst, sport, dport, proto, size = tup
        direction = "fwd" if src in local_ips else "bwd"
        ts = time.time()
        aggregator.push_packet(src, dst, sport, dport, proto, size, direction, ts=ts)

        ready = aggregator.extract_ready_flows()
        if ready:
            rows = []
            for f in ready:
                rec = f.to_dict()

                if analyzer:
                    try:
                        score = analyzer.score(rec)
                        label = analyzer.label_from_score(score)
                    except Exception as e:
                        score = -1.0
                        label = "unknown"
                else:
                    score = -1.0
                    label = "unknown"

                rec["anomaly_score"] = float(score)
                rec["label"] = label

                # Dodajemy timestamp
                rec["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                try:
                    controller.react(rec, label)
                except Exception as e:
                    print("[capture_live] controller error:", e)

                rows.append(rec)

            with open(OUTPUT_FILE, "a", newline="") as f:
                writer = csv.writer(f)
                for r in rows:
                    writer.writerow([r.get(col, "") for col in FEATURES])

    print("[capture_live] starting sniff()")
    try:
        sniff(iface=iface, prn=handle, store=False)
    except KeyboardInterrupt:
        print("[capture_live] stopped by user")
        remaining = aggregator.force_close_all()
        with open(OUTPUT_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            for fobj in remaining:
                rec = fobj.to_dict()
                rec["anomaly_score"] = -1.0
                rec["label"] = "flushed"
                rec["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                writer.writerow([rec.get(col, "") for col in FEATURES])

if __name__ == "__main__":
    main()
