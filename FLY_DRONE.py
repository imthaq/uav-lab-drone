#!/usr/bin/env python3
"""
hardware_integration_test.py
"""

import argparse
import time

from dronekit import connect, VehicleMode, LocationGlobalRelative
import geopy.distance

CANDIDATE_DEVICES = ["/dev/serial0", "/dev/ttyAMA0"]
CANDIDATE_BAUD_RATES = [57600, 115200]
CONNECT_TIMEOUT = 60  
TARGET_ALTITUDE_M = 3  
DISTANCE_THRESHOLD_M = 2  

def is_serial_connection_string(conn_str):
    return not (conn_str.startswith("udp:") or conn_str.startswith("tcp:")
                or conn_str.startswith("udpin:") or conn_str.startswith("udpout:"))

def build_candidate_list(connection_string):
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
    parser = argparse.ArgumentParser(description="Connect to drone and fly to target location")
    parser.add_argument('--connect', help="vehicle connection target string")
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

    raise RuntimeError("Could not connect to vehicle. Pass --connect explicitly.")

def attach_statustext_listener(vehicle):
    last_statustext = {"text": None}
    def _on_statustext(_vehicle, _name, message):
        if message is not None:
            text = message.text.strip()
            last_statustext["text"] = text
            print(f" [autopilot] {text}")
    vehicle.add_message_listener('STATUSTEXT', _on_statustext)
    return last_statustext

def arm_and_takeoff(vehicle, target_altitude, arm_timeout=60):
    last_statustext = attach_statustext_listener(vehicle)
    print("Basic pre-arm checks")
    waited = 0
    while not vehicle.is_armable:
        gps = vehicle.gps_0
        print(f" Waiting for vehicle to initialise... gps_fix={gps.fix_type}")
        if waited >= arm_timeout:
            raise TimeoutError("Vehicle not armable. Check GPS/Compass/EKF.")
        time.sleep(2)
        waited += 2

    print("Arming motors")
    vehicle.mode = VehicleMode("GUIDED")
    
    # FIX: Wait for GUIDED mode
    waited = 0
    while vehicle.mode.name != "GUIDED":
        if waited >= arm_timeout:
            raise TimeoutError("Failed to enter GUIDED mode.")
        time.sleep(1)
        waited += 1

    vehicle.armed = True

    # FIX: Uncommented arming loop
    waited = 0
    while not vehicle.armed:
        print(f" Waiting for arming... mode={vehicle.mode.name} last_msg={last_statustext['text']!r}")
        if waited >= arm_timeout:
            raise TimeoutError("Arm command not accepted.")
        time.sleep(2)
        waited += 2

    print("Taking off!")
    vehicle.simple_takeoff(target_altitude)

    # FIX: Added timeout to altitude loop
    waited = 0
    while True:
        current_alt = vehicle.location.global_relative_frame.alt
        print(f" Altitude: {current_alt}")
        if current_alt >= target_altitude * 0.95:
            print("Reached target altitude")
            break
        if waited >= 60:
            print("Warning: Timeout reaching target altitude.")
            break
        time.sleep(1)
        waited += 1

def get_distance_m(coord1, coord2):
    return geopy.distance.geodesic(coord1, coord2).km * 1000

def goto_location(vehicle, to_lat, to_lon, timeout=120):
    print(f" Global Location (relative altitude): {vehicle.location.global_relative_frame}")
    curr_alt = vehicle.location.global_relative_frame.alt
    target_point = LocationGlobalRelative(to_lat, to_lon, curr_alt)
    vehicle.simple_goto(target_point, groundspeed=1)
    target_coord = (to_lat, to_lon)
    
    # FIX: Added timeout to arrival loop
    waited = 0
    while True:
        curr_lat = vehicle.location.global_relative_frame.lat
        curr_lon = vehicle.location.global_relative_frame.lon
        curr_coord = (curr_lat, curr_lon)
        distance = get_distance_m(curr_coord, target_coord)
        print(f"curr location: {curr_coord} | distance remaining: {distance:.1f} m")
        if distance <= DISTANCE_THRESHOLD_M:
            print(f"Reached within {DISTANCE_THRESHOLD_M} meters of target location...")
            break
        if waited >= timeout:
            print("Warning: Timeout reaching target destination.")
            break
        time.sleep(1)
        waited += 1

def run_mission(vehicle):
    arm_and_takeoff(vehicle, TARGET_ALTITUDE_M)
    
    # FIX: Dynamic local waypoint instead of a hardcoded cross-world GPS coordinate
    current_loc = vehicle.location.global_relative_frame
    target_lat = current_loc.lat + 0.0001
    target_lon = current_loc.lon + 0.0001
    
    print(f"Navigating to local offset waypoint: {target_lat}, {target_lon}")
    goto_location(vehicle, target_lat, target_lon)
    
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