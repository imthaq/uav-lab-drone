#!/usr/bin/env python3
"""
Simple Pixhawk connection test.

Requires: pip install pymavlink

Usage:
    python pixhawk_connection_test.py [connection_string]

Examples:
    python pixhawk_connection_test.py /dev/ttyACM0
    python pixhawk_connection_test.py udp:127.0.0.1:14550
    python pixhawk_connection_test.py COM3
"""

import sys
from pymavlink import mavutil

# Default connection - change as needed, or pass as a command-line argument
CONNECTION_STRING = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyACM0"
BAUD_RATE = 57600  # ignored for udp/tcp connections

def main():
    print(f"Connecting to Pixhawk on {CONNECTION_STRING} ...")

    master = mavutil.mavlink_connection(CONNECTION_STRING, baud=BAUD_RATE)

    print("Waiting for heartbeat...")
    master.wait_heartbeat()

    print("Heartbeat received!")
    print(f"  System ID:    {master.target_system}")
    print(f"  Component ID: {master.target_component}")

    master.close()
    print("Connection closed.")

if __name__ == "__main__":
    main()
