#!/usr/bin/env python3

from scapy.all import *
import time
import random
import os

TARGET_IP = "127.0.0.1"
TARGET_PORT = 4444  # typowe porty C&C

def botnet_ares():
    print("[*] Starting CICIDS2018-style Botnet ARES simulation...")

    while True:
        # beacon (mały pakiet kontrolny)
        sport = 65000
        beacon = IP(dst=TARGET_IP)/TCP(sport=sport, dport=TARGET_PORT, flags="PA")/Raw(
            load=b"beacon:" + os.urandom(random.randint(4, 12))
        )
        send(beacon, verbose=0)
        print("[+] Beacon sent")

        time.sleep(random.uniform(0.3, 1.2))

        # C2 payload (też krótki)
        c2 = IP(dst=TARGET_IP)/TCP(sport=sport, dport=TARGET_PORT, flags="PA")/Raw(
            load=b"cmd:" + os.urandom(random.randint(20, 80))
        )
        send(c2, verbose=0)
        print("[+] C2 command sent")

        # random sleep imitujący nieregularny ruch botnetu
        time.sleep(random.uniform(0.5, 2.0))


if __name__ == "__main__":
    botnet_ares()
