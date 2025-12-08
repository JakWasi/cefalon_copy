# src/control/decision_controller.py
import subprocess
import threading
import time
import os

# SAFE DEFAULT: do not run iptables commands unless explicitly enabled.
ENABLE_ACTIVE_BLOCKING = False

class DecisionController:
    """
    Controller to react to labels for a given IP.
    - block_ip(ip): add a DROP rule (if ENABLE_ACTIVE_BLOCKING True)
    - allow_ip(ip): remove that rule
    - temporary_block(ip, seconds): block then schedule unblock
    """

    def __init__(self, iface=None):
        self._blocked = set()
        self._timers = {}
        self.iface = iface  # optional: interface to scope rules

    def _run_cmd(self, cmd):
        try:
            subprocess.run(cmd, check=True)
            return True
        except Exception as e:
            print("[DecisionController] Command failed:", e)
            return False

    def block_ip(self, ip: str):
        print(f"[DecisionController] block_ip: {ip}")
        self._blocked.add(ip)
        if ENABLE_ACTIVE_BLOCKING:
            # Add an iptables rule to DROP traffic from ip (INPUT chain).
            # NOTE: you need root to run these commands.
            cmd = ["sudo", "iptables", "-I", "INPUT", "-s", ip, "-j", "DROP"]
            if self.iface:
                cmd[2:2] = ["-i", self.iface]  # insert interface option if provided
            self._run_cmd(cmd)

    def allow_ip(self, ip: str):
        print(f"[DecisionController] allow_ip: {ip}")
        if ip in self._blocked:
            self._blocked.remove(ip)
        if ENABLE_ACTIVE_BLOCKING:
            # Try to remove any matching DROP rules (best-effort)
            # This naive removal may need adaptation to your iptables rule ordering.
            cmd = ["sudo", "iptables", "-D", "INPUT", "-s", ip, "-j", "DROP"]
            if self.iface:
                cmd[2:2] = ["-i", self.iface]
            # run repeatedly until it fails to try removing duplicates
            while True:
                try:
                    subprocess.run(cmd, check=True)
                except Exception:
                    break

    def temporary_block(self, ip: str, duration: int):
        print(f"[DecisionController] temporary_block: {ip} for {duration}s")
        self.block_ip(ip)
        if ip in self._timers:
            self._timers[ip].cancel()
        timer = threading.Timer(duration, lambda: self._release_temp(ip))
        self._timers[ip] = timer
        timer.daemon = True
        timer.start()

    def _release_temp(self, ip: str):
        self.allow_ip(ip)
        if ip in self._timers:
            del self._timers[ip]

    def react(self, flow_dict, label: str):
        """
        flow_dict should include 'src_ip' key.
        Policy:
          - attack -> immediate block (permanent)
          - suspicious -> temporary block (30s)
          - benign -> ensure allowed (remove block)
        """
        ip = flow_dict.get("src_ip")
        if not ip:
            return
        if label == "attack":
            self.block_ip(ip)
        elif label == "suspicious":
            self.temporary_block(ip, 30)
        else:
            # benign
            self.allow_ip(ip)
