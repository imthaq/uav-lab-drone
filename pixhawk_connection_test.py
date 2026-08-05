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


def decode_flight_mode(master, msg):
    """Return a human-readable flight mode name for the current autopilot."""
    try:
        mode_str = mavutil.mode_string_v10(msg)
    except Exception:
        mode_str = None
    return mode_str if mode_str else f"UNKNOWN(custom_mode={msg.custom_mode})"


def is_armed(msg):
    """Return True if the ARMED safety bit is set in base_mode."""
    return bool(msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED)


def main():
    print(f"Connecting to Pixhawk on {CONNECTION_STRING} ...")

    master = mavutil.mavlink_connection(CONNECTION_STRING, baud=BAUD_RATE)

    print("Waiting for heartbeat...")
    msg = master.wait_heartbeat(timeout=10)

    if msg is None:
        print("No heartbeat received within timeout. Check wiring, baud rate, "
              "and SERIAL2_PROTOCOL/SERIAL2_BAUD on the Pixhawk.")
        master.close()
        return

    # Force target_component to the real autopilot component,
    # in case the heartbeat reported 0 (broadcast/all).
    master.target_component = 1

    flight_mode = decode_flight_mode(master, msg)
    armed = is_armed(msg)

    print("Heartbeat received!")
    print(f"  System ID:    {master.target_system}")
    print(f"  Component ID (raw from heartbeat): {msg.get_srcComponent()}")
    print(f"  Component ID (forced for commands): {master.target_component}")
    print(f"  Autopilot type: {msg.autopilot}")
    print(f"  Vehicle type:   {msg.type}")
    print(f"  Base mode:      {msg.base_mode}")
    print(f"  System status:  {msg.system_status}")
    print(f"  Flight mode:    {flight_mode}")
    print(f"  Armed:          {armed}")

    master.close()
    print("Connection closed.")


if __name__ == "__main__":
    main()