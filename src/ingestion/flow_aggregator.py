# src/ingestion/flow_aggregator.py
import time
from dataclasses import dataclass, field
from typing import Dict, Tuple, List


@dataclass
class Flow:
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocol: int
    start_time: float = field(default_factory=time.time)
    end_time: float = field(default_factory=time.time)
    tot_fwd_pkts: int = 0
    tot_bwd_pkts: int = 0
    src_bytes: int = 0
    dst_bytes: int = 0

    @property
    def duration(self) -> float:
        return max(0.0, self.end_time - self.start_time)

    @property
    def total_pkts(self) -> int:
        return self.tot_fwd_pkts + self.tot_bwd_pkts

    @property
    def total_bytes(self) -> int:
        return self.src_bytes + self.dst_bytes

    def to_dict(self) -> Dict:
        return {
            "duration": float(self.duration),
            "tot_fwd_pkts": int(self.tot_fwd_pkts),
            "tot_bwd_pkts": int(self.tot_bwd_pkts),
            "src_bytes": int(self.src_bytes),
            "dst_bytes": int(self.dst_bytes),
            "total_pkts": int(self.total_pkts),
            "total_bytes": int(self.total_bytes),
            "protocol": int(self.protocol),
            "src_ip": self.src_ip,
            "dst_ip": self.dst_ip,
            "src_port": int(self.src_port),
            "dst_port": int(self.dst_port),
        }


class FlowAggregator:
    """
    Simple 5-tuple flow aggregator. Keyed by (src, dst, sport, dport, proto).
    A flow is closed and returned by extract_ready_flows when no packets seen
    for `timeout` seconds.
    """

    def __init__(self, timeout: int = 30):
        self.timeout = float(timeout)
        self._flows: Dict[Tuple, Flow] = {}
        self._last_seen: Dict[Tuple, float] = {}

    def _key(self, src_ip, dst_ip, src_port, dst_port, proto):
        return (src_ip, dst_ip, int(src_port or 0), int(dst_port or 0), int(proto or 0))

    def push_packet(self, src_ip, dst_ip, src_port, dst_port, proto, size, direction, ts=None):
        ts = float(ts or time.time())
        k = self._key(src_ip, dst_ip, src_port, dst_port, proto)
        if k not in self._flows:
            f = Flow(src_ip=src_ip, dst_ip=dst_ip, src_port=src_port or 0,
                     dst_port=dst_port or 0, protocol=int(proto or 0),
                     start_time=ts, end_time=ts)
            self._flows[k] = f
            self._last_seen[k] = ts
        else:
            f = self._flows[k]
            f.end_time = ts
            self._last_seen[k] = ts

        if direction == "fwd":
            f.tot_fwd_pkts += 1
            f.src_bytes += int(size or 0)
        else:
            f.tot_bwd_pkts += 1
            f.dst_bytes += int(size or 0)

    def extract_ready_flows(self) -> List[Flow]:
        """
        Return flows that are idle for >= timeout seconds and remove them from memory.
        """
        now = time.time()
        ready = []
        for k, last in list(self._last_seen.items()):
            if (now - last) >= self.timeout:
                f = self._flows.pop(k)
                self._last_seen.pop(k)
                ready.append(f)
        return ready

    def force_close_all(self) -> List[Flow]:
        """
        Force-close everything (used on shutdown).
        """
        all_flows = list(self._flows.values())
        self._flows.clear()
        self._last_seen.clear()
        return all_flows
