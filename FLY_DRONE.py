#!/usr/bin/env python3
"""
hardware_integration_test.py

Connects to the flight controller (Pixhawk), arms the vehicle, takes off,
and flies to a pre-defined GPS location, then returns to launch.

Connection handling borrows the robust device/baud probing approach from
pixhawk_connection_test.py: if no --connect string is supplied on the
command line, the script tries each candidate serial device at each
candidate baud rate until one produces a working connection. If a
--connect string IS supplied, it is tried directly (at both candidate
baud rates if it looks like a serial device rather than udp/tcp).

Requires: pip install dronekit geopy pymavlink

Usage:
    python hardware_integration_test.py                       # auto-probe devices/baud rates
    python hardware_integration_test.py --connect /dev/ttyAMA0  # test only this device
    python hardware_integration_test.py --connect udp:127.0.0.1:14550
"""

import argparse
import time

from dronekit import connect, VehicleMode, LocationGlobalRelative
import geopy.distance

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
# Candidate serial devices / baud rates to probe when no --connect string is
# supplied on the CLI (mirrors pixhawk_connection_test.py).
CANDIDATE_DEVICES = ["/dev/serial0", "/dev/ttyAMA0"]
CANDIDATE_BAUD_RATES = [57600, 115200]

CONNECT_TIMEOUT = 60  # seconds to wait for dronekit's wait_ready per attempt

# Target location for the mission (previously hard-coded inside my_mission()).
TARGET_LATITUDE = 25.806476
TARGET_LONGITUDE = 86.778428
TARGET_ALTITUDE_M = 3  # takeoff / cruise altitude in meters

DISTANCE_THRESHOLD_M = 2  # how close counts as "arrived"


# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------
def is_serial_connection_string(conn_str):
    """UDP/TCP connection strings don't have a baud rate, so we skip the
    baud-rate probing for those and only try them once."""
    return not (conn_str.startswith("udp:") or conn_str.startswith("tcp:")
                or conn_str.startswith("udpin:") or conn_str.startswith("udpout:"))


def build_candidate_list(connection_string):
    """Return a list of (device, baud) tuples to try, in order."""
    if connection_string:
        if not is_serial_connection_string(connection_string):
            return [(connection_string, None)]
        return [(connection_string, baud) for baud in CANDIDATE_BAUD_RATES]

    candidates = []
    for device in CANDIDATE_DEVICES:
        for baud in CANDIDATE_BAUD_RATES:
            candidates.append((device, baud))
    return candidates


def connect_to_vehicle():
    """
    Parse --connect from the CLI. If given, try it (at both candidate baud
    rates if it's a serial device). If not given, probe the candidate
    devices/baud rates in turn until one connects successfully.
    """
    parser = argparse.ArgumentParser(description="Connect to drone and fly to target location")
    parser.add_argument('--connect',
                         help="vehicle connection target string, e.g. /dev/ttyAMA0 or udp:127.0.0.1:14550")
    args = parser.parse_args()

    candidates = build_candidate_list(args.connect)

    for device, baud in candidates:
        label = f"{device} @ {baud or 'default'} baud"
        print(f"\nConnecting to vehicle on: {label}")
        try:
            if baud is not None:
                vehicle = connect(device, baud=baud, wait_ready=True, timeout=CONNECT_TIMEOUT)
            else:
                vehicle = connect(device, wait_ready=True, timeout=CONNECT_TIMEOUT)
            print(f"Connected on {label}")
            return vehicle
        except Exception as e:
            print(f"Failed to connect on {label}: {type(e).__name__}: {e}")

    raise RuntimeError(
        "Could not connect to vehicle on any candidate device/baud rate. "
        "Check wiring, and SERIAL2_PROTOCOL / SERIAL2_BAUD on the Pixhawk, "
        "or pass --connect explicitly."
    )


# ---------------------------------------------------------------------------
# Flight helpers
# ---------------------------------------------------------------------------
def arm_and_takeoff(vehicle, target_altitude):
    """Arms vehicle and flies to target_altitude (meters, relative)."""
    print("Basic pre-arm checks")
    while not vehicle.is_armable:
        print(" Waiting for vehicle to initialise...")
        time.sleep(1)

    print("Arming motors")
    vehicle.mode = VehicleMode("GUIDED")
    vehicle.armed = True

    while not vehicle.armed:
        print(" Waiting for arming...")
        time.sleep(1)

    print("Taking off!")
    vehicle.simple_takeoff(target_altitude)

    # Wait until the vehicle reaches a safe height before commanding goto,
    # otherwise the next command executes immediately.
    while True:
        current_alt = vehicle.location.global_relative_frame.alt
        print(f" Altitude: {current_alt}")
        if current_alt >= target_altitude * 0.95:
            print("Reached target altitude")
            break
        time.sleep(1)


def get_distance_m(coord1, coord2):
    """Distance in meters between two (lat, lon) tuples."""
    return geopy.distance.geodesic(coord1, coord2).km * 1000


def goto_location(vehicle, to_lat, to_lon):
    """Fly to (to_lat, to_lon) at current altitude, blocking until arrival."""
    print(f" Global Location (relative altitude): {vehicle.location.global_relative_frame}")
    curr_alt = vehicle.location.global_relative_frame.alt

    target_point = LocationGlobalRelative(to_lat, to_lon, curr_alt)
    vehicle.simple_goto(target_point, groundspeed=1)

    target_coord = (to_lat, to_lon)
    while True:
        curr_lat = vehicle.location.global_relative_frame.lat
        curr_lon = vehicle.location.global_relative_frame.lon
        curr_coord = (curr_lat, curr_lon)
        distance = get_distance_m(curr_coord, target_coord)
        print(f"curr location: {curr_coord} | distance remaining: {distance:.1f} m")
        if distance <= DISTANCE_THRESHOLD_M:
            print(f"Reached within {DISTANCE_THRESHOLD_M} meters of target location...")
            break
        time.sleep(1)


# ---------------------------------------------------------------------------
# Mission
# ---------------------------------------------------------------------------
def run_mission(vehicle):
    arm_and_takeoff(vehicle, TARGET_ALTITUDE_M)
    goto_location(vehicle, TARGET_LATITUDE, TARGET_LONGITUDE)
    print("Returning to Launch")
    vehicle.mode = VehicleMode("RTL")


def main():
    vehicle = connect_to_vehicle()
    try:
        run_mission(vehicle)
    finally:
        vehicle.close()


if __name__ == "__main__":
    main()
