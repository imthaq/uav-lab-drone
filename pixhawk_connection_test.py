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
CONNECTION_STRING = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyAMA0"
BAUD_RATE = 57600  # ignored for udp/tcp connections

def main():
    print(f"Connecting to Pixhawk on {CONNECTION_STRING} ...")

    master = mavutil.mavlink_connection(CONNECTION_STRING, baud=BAUD_RATE)

    print("Waiting for heartbeat...")
    msg = master.wait_heartbeat()

    # Force target_component to the real autopilot component,
    # in case the heartbeat reported 0 (broadcast/all).
    master.target_component = 1

    print("Heartbeat received!")
    print(f"  System ID:    {master.target_system}")
    print(f"  Component ID (raw from heartbeat): {msg.get_srcComponent()}")
    print(f"  Component ID (forced for commands): {master.target_component}")
    print(f"  Autopilot type: {msg.autopilot}")
    print(f"  Vehicle type:   {msg.type}")
    print(f"  Base mode:      {msg.base_mode}")
    print(f"  System status:  {msg.system_status}")

    master.close()
    print("Connection closed.")

if __name__ == "__main__":
    main()
