#!/usr/bin/env python3
"""
pixhawk_connection_test.py

Task 11 - Improve Pixhawk connection stability.

Tries each candidate serial device against each candidate baud rate until
a MAVLink heartbeat is received, then stays connected and monitors the
link continuously. A single missed heartbeat no longer crashes the
program: it is logged as a heartbeat timeout and the script attempts to
reconnect after a short delay, retrying indefinitely.

Requires: pip install pymavlink

Usage:
    python pixhawk_connection_test.py                  # auto-probe devices/baud rates
    python pixhawk_connection_test.py /dev/ttyAMA0      # test only this device (still tries both baud rates)
    python pixhawk_connection_test.py udp:127.0.0.1:14550  # non-serial connection strings skip baud probing
"""

import sys
import csv
import time
import os

from pymavlink import mavutil

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
# Devices to probe, in order, when no connection string is given on the CLI.
CANDIDATE_DEVICES = ["/dev/serial0", "/dev/ttyAMA0"]

# Baud rates to try against each device: 57600 first, 115200 as a fallback.
CANDIDATE_BAUD_RATES = [57600, 115200]

INITIAL_HEARTBEAT_TIMEOUT = 10   # seconds to wait for the first heartbeat while probing
MONITOR_HEARTBEAT_TIMEOUT = 5    # seconds without a heartbeat before we call the link lost, once connected
RECONNECT_DELAY = 5              # seconds to wait between reconnection attempts
LOOP_POLL_INTERVAL = 0.5         # seconds between non-blocking heartbeat checks

CSV_FILENAME = "pixhawk_connection_log.csv"

CSV_FIELDS = [
    "timestamp", "event", "device", "baud",
    "connection_start_time", "heartbeat_received_time",
    "system_id", "component_id", "flight_mode", "armed",
    "detail",
]


# ---------------------------------------------------------------------------
# CSV logging
# ---------------------------------------------------------------------------
def init_csv():
    if not os.path.isfile(CSV_FILENAME):
        with open(CSV_FILENAME, mode="w", newline="") as f:
            csv.writer(f).writerow(CSV_FIELDS)


def log_event(event, device="", baud="", connection_start_time="",
              heartbeat_received_time="", system_id="", component_id="",
              flight_mode="", armed="", detail=""):
    """Append one row to the CSV log and echo it to the console."""
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    row = [
        now, event, device, baud,
        connection_start_time, heartbeat_received_time,
        system_id, component_id, flight_mode, armed, detail,
    ]
    with open(CSV_FILENAME, mode="a", newline="") as f:
        csv.writer(f).writerow(row)

    print(f"{now} | {event:18s} | device={device} baud={baud} "
          f"sysid={system_id} compid={component_id} mode={flight_mode} "
          f"armed={armed} {('| ' + detail) if detail else ''}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def decode_flight_mode(msg):
    try:
        mode_str = mavutil.mode_string_v10(msg)
    except Exception:
        mode_str = None
    return mode_str if mode_str else f"UNKNOWN(custom_mode={msg.custom_mode})"


def is_armed(msg):
    return bool(msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED)


def is_serial_connection_string(conn_str):
    """UDP/TCP connection strings don't have a baud rate, so we skip the
    baud-rate probing loop for those and only try them once."""
    return not (conn_str.startswith("udp:") or conn_str.startswith("tcp:")
                or conn_str.startswith("udpin:") or conn_str.startswith("udpout:"))


def build_candidate_list():
    """Return a list of (device, baud) tuples to try, in order."""
    if len(sys.argv) > 1:
        conn_str = sys.argv[1]
        if not is_serial_connection_string(conn_str):
            return [(conn_str, None)]
        return [(conn_str, baud) for baud in CANDIDATE_BAUD_RATES]

    candidates = []
    for device in CANDIDATE_DEVICES:
        for baud in CANDIDATE_BAUD_RATES:
            candidates.append((device, baud))
    return candidates


# ---------------------------------------------------------------------------
# Connection attempt (probing phase)
# ---------------------------------------------------------------------------
def try_connect(device, baud):
    """Attempt a single connection + heartbeat wait against one
    (device, baud) combination. Returns (master, msg) on success, or
    (None, None) on failure. Never raises - all errors are logged."""
    connection_start_time = time.strftime("%Y-%m-%d %H:%M:%S")
    log_event("connection_start", device=device, baud=baud or "-",
              connection_start_time=connection_start_time)

    master = None
    try:
        if baud is not None:
            master = mavutil.mavlink_connection(device, baud=baud)
        else:
            master = mavutil.mavlink_connection(device)
    except Exception as e:
        # e.g. device does not exist, permission denied, port busy
        log_event("serial_error", device=device, baud=baud or "-",
                  connection_start_time=connection_start_time,
                  detail=f"{type(e).__name__}: {e}")
        return None, None

    try:
        msg = master.wait_heartbeat(timeout=INITIAL_HEARTBEAT_TIMEOUT)
    except Exception as e:
        log_event("serial_error", device=device, baud=baud or "-",
                  connection_start_time=connection_start_time,
                  detail=f"error while waiting for heartbeat: {e}")
        try:
            master.close()
        except Exception:
            pass
        return None, None

    if msg is None:
        log_event("heartbeat_timeout", device=device, baud=baud or "-",
                  connection_start_time=connection_start_time,
                  detail=f"no heartbeat within {INITIAL_HEARTBEAT_TIMEOUT}s")
        try:
            master.close()
        except Exception:
            pass
        return None, None

    master.target_component = 1
    heartbeat_received_time = time.strftime("%Y-%m-%d %H:%M:%S")
    flight_mode = decode_flight_mode(msg)
    armed = is_armed(msg)

    log_event("heartbeat_received", device=device, baud=baud or "-",
              connection_start_time=connection_start_time,
              heartbeat_received_time=heartbeat_received_time,
              system_id=master.target_system,
              component_id=master.target_component,
              flight_mode=flight_mode, armed=armed)

    return master, msg


def probe_candidates():
    """Try every (device, baud) candidate in order until one succeeds.
    Returns (master, device, baud, msg) for the working combination, or
    (None, None, None, None) if every candidate failed."""
    for device, baud in build_candidate_list():
        master, msg = try_connect(device, baud)
        if master is not None:
            return master, device, baud, msg
    return None, None, None, None


# ---------------------------------------------------------------------------
# Monitoring loop - stays connected, survives missed heartbeats
# ---------------------------------------------------------------------------
def monitor(master, device, baud, initial_msg=None):
    """Continuously watch the link. A missed heartbeat is logged and
    triggers a reconnect attempt after RECONNECT_DELAY - it never crashes
    the program. An armed/disarmed transition is logged the moment it is
    observed, not just on the next timeout/reconnect event."""
    last_heartbeat_time = time.time()
    connected = True
    last_reconnect_attempt = 0.0
    system_id = master.target_system
    component_id = master.target_component

    # Seed flight_mode/armed from the heartbeat we already received during
    # connection, rather than resetting to UNKNOWN/False.
    if initial_msg is not None:
        flight_mode = decode_flight_mode(initial_msg)
        armed = is_armed(initial_msg)
    else:
        flight_mode = "UNKNOWN"
        armed = False

    print("Monitoring Pixhawk link. Press Ctrl+C to stop.")

    while True:
        if connected:
            try:
                msg = master.recv_match(type="HEARTBEAT", blocking=False)
            except Exception as e:
                log_event("serial_error", device=device, baud=baud or "-",
                          detail=f"link dropped: {e}")
                connected = False
                master = None
            else:
                if msg is not None:
                    last_heartbeat_time = time.time()
                    new_flight_mode = decode_flight_mode(msg)
                    new_armed = is_armed(msg)

                    if new_armed != armed:
                        log_event("armed_status_change", device=device, baud=baud or "-",
                                  system_id=system_id, component_id=component_id,
                                  flight_mode=new_flight_mode, armed=new_armed,
                                  detail=f"changed from {armed} to {new_armed}")

                    flight_mode, armed = new_flight_mode, new_armed

                elif time.time() - last_heartbeat_time > MONITOR_HEARTBEAT_TIMEOUT:
                    # Missed heartbeat(s) - log it and drop to reconnect mode,
                    # but do NOT crash or exit.
                    log_event("heartbeat_timeout", device=device, baud=baud or "-",
                              system_id=system_id, component_id=component_id,
                              flight_mode=flight_mode, armed=armed,
                              detail=f"no heartbeat for over {MONITOR_HEARTBEAT_TIMEOUT}s")
                    connected = False

        if not connected:
            now = time.time()
            if now - last_reconnect_attempt >= RECONNECT_DELAY:
                last_reconnect_attempt = now
                log_event("reconnect_attempt", device=device, baud=baud or "-",
                          detail="attempting to reconnect")

                new_master, msg = try_connect(device, baud)
                if new_master is not None:
                    master = new_master
                    system_id = master.target_system
                    component_id = master.target_component
                    flight_mode = decode_flight_mode(msg)
                    armed = is_armed(msg)
                    last_heartbeat_time = time.time()
                    connected = True
                    log_event("reconnect_attempt", device=device, baud=baud or "-",
                              system_id=system_id, component_id=component_id,
                              flight_mode=flight_mode, armed=armed,
                              detail="SUCCESS")
                else:
                    log_event("reconnect_attempt", device=device, baud=baud or "-",
                              detail="FAILED")

        time.sleep(LOOP_POLL_INTERVAL)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    init_csv()

    print("Probing for Pixhawk connection...")
    master, device, baud, initial_msg = probe_candidates()

    if master is None:
        print("Could not establish a Pixhawk connection on any candidate "
              "device/baud rate. Check wiring, and SERIAL2_PROTOCOL / "
              "SERIAL2_BAUD on the Pixhawk. See pixhawk_connection_log.csv "
              "for details of every attempt.")
        return

    print(f"Connected on {device} @ {baud or 'default'} baud.")

    try:
        monitor(master, device, baud, initial_msg=initial_msg)
    except KeyboardInterrupt:
        print("\nStopped by user.")
    finally:
        if master is not None:
            try:
                master.close()
            except Exception:
                pass


if __name__ == "__main__":
    main()