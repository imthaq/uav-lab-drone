#!/usr/bin/env python3
"""
hardware_integration_test.py

Full hardware integration test: VL53L0X sensors (front/left/right/back via
TCA9548A), camera capture on WARNING/DANGER, and Pixhawk MAVLink status —
all logged to CSV in one loop.

Task 12 — Reconnect behavior:
If the Pixhawk connection is lost mid-run:
  * Pixhawk status is marked DISCONNECTED
  * sensor logging continues normally (sensors are independent of the Pixhawk link)
  * no movement decision is issued — decision is forced to
    "HOLD / CONNECTION FAULT" regardless of sensor readings
  * reconnection is attempted after a short delay (not every loop iteration,
    to avoid hammering the serial port)
  * the result of each reconnection attempt (SUCCESS/FAILED) is recorded in the CSV

Requires: pip install pymavlink adafruit-circuitpython-tca9548a adafruit-circuitpython-vl53l0x
"""

import os
import sys
import csv
import time
import subprocess

import board
import busio
import adafruit_tca9548a
import adafruit_vl53l0x
from pymavlink import mavutil

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
PIXHAWK_CONNECTION_STRING = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyAMA0"
PIXHAWK_BAUD_RATE = 57600
HEARTBEAT_TIMEOUT = 3.0          # seconds without a heartbeat before we call it lost
RECONNECT_INTERVAL = 5.0         # seconds between reconnection attempts while disconnected

SAFE_THRESHOLD = 700
DANGER_THRESHOLD = 300
CSV_FILENAME = "hardware_integration_log.csv"
IMAGE_DIR = "captures"
LOOP_DELAY = 0.5

# ---------------------------------------------------------------------------
# TCA9548A channel mapping — the single source of truth for sensor position.
# All sensor init/read/log logic below reads from this dict; no channel
# numbers are hardcoded anywhere else in the file. To physically re-map a
# sensor (e.g. swap left/right), change it here only.
# ---------------------------------------------------------------------------
CHANNEL_MAP = {
    'front': 0,
    'left': 1,
    'right': 2,
    'back': 3,
}

os.makedirs(IMAGE_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# Sensor / camera hardware — positions and channels driven by CHANNEL_MAP
# ---------------------------------------------------------------------------
def initialize_sensor_hardware():
    hw = {'i2c': None, 'tca': None, 'status': "OK"}
    for position in CHANNEL_MAP:
        hw[position] = None

    try:
        hw['i2c'] = busio.I2C(board.SCL, board.SDA)
        hw['tca'] = adafruit_tca9548a.TCA9548A(hw['i2c'])

        for position, channel in CHANNEL_MAP.items():
            try:
                hw[position] = adafruit_vl53l0x.VL53L0X(hw['tca'][channel])
            except Exception:
                hw['status'] = f"{position.upper()}_SENSOR_ERROR"

    except Exception as e:
        print(f"CRITICAL SENSOR_ERROR (I2C/TCA): {e}")
        hw['status'] = "CRITICAL_I2C_ERROR"

    return hw


def get_status(distance):
    if distance is None:
        return "ERROR"
    if distance > SAFE_THRESHOLD:
        return "SAFE"
    elif DANGER_THRESHOLD <= distance <= SAFE_THRESHOLD:
        return "WARNING"
    else:
        return "DANGER"


def determine_logic(f_stat, l_stat, r_stat, b_stat):
    statuses = [f_stat, l_stat, r_stat, b_stat]
    danger_count = statuses.count("DANGER")

    if "DANGER" in statuses:
        overall = "DANGER"
    elif "WARNING" in statuses:
        overall = "WARNING"
    elif "ERROR" in statuses:
        overall = "ERROR"
    else:
        overall = "SAFE"

    if danger_count > 1 or f_stat == "DANGER":
        decision = "STOP / HOLD"
    elif l_stat == "DANGER":
        decision = "MOVE RIGHT"
    elif r_stat == "DANGER":
        decision = "MOVE LEFT"
    elif b_stat == "DANGER":
        decision = "HOLD POSITION (NO REVERSE)"
    elif f_stat == "WARNING":
        decision = "SLOW / CAUTION"
    elif l_stat == "WARNING":
        decision = "SLIGHT RIGHT CORRECTION"
    elif r_stat == "WARNING":
        decision = "SLIGHT LEFT CORRECTION"
    elif b_stat == "WARNING":
        decision = "CAUTION REVERSE"
    elif overall == "SAFE":
        decision = "MOVE FORWARD"
    else:
        decision = "UNKNOWN"

    return overall, decision


def capture_image():
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    filename = f"{IMAGE_DIR}/alert_{timestamp}.jpg"
    try:
        result = subprocess.run(
            ["rpicam-still", "-o", filename, "--nopreview", "-t", "500", "--vflip"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            return filename
        print(f"CAMERA_ERROR details: {result.stderr.strip()}")
        return "CAMERA_ERROR"
    except FileNotFoundError:
        return "CAMERA_ERROR (Command not found)"
    except Exception as e:
        print(f"CAMERA_ERROR: {e}")
        return "CAMERA_ERROR"


# ---------------------------------------------------------------------------
# Pixhawk link with reconnect behavior (Task 12)
# ---------------------------------------------------------------------------
class PixhawkLink:
    """Wraps a MAVLink connection and tracks CONNECTED / DISCONNECTED state,
    handling reconnection attempts without blocking sensor logging."""

    def __init__(self, connection_string, baud):
        self.connection_string = connection_string
        self.baud = baud
        self.master = None
        self.status = "DISCONNECTED"
        self.flight_mode = "UNKNOWN"
        self.armed = False
        self.last_heartbeat_time = 0.0
        self.last_reconnect_attempt = 0.0
        self.reconnect_result = "N/A"

        self._connect()

    def _connect(self):
        """Attempt a fresh connection + initial heartbeat. Never raises."""
        try:
            if self.master is not None:
                try:
                    self.master.close()
                except Exception:
                    pass
            self.master = mavutil.mavlink_connection(self.connection_string, baud=self.baud)
            msg = self.master.wait_heartbeat(timeout=5)
            if msg is None:
                raise TimeoutError("No heartbeat within timeout")

            self.master.target_component = 1
            self._update_from_heartbeat(msg)
            self.status = "CONNECTED"
            self.reconnect_result = "SUCCESS"
            return True
        except Exception as e:
            self.master = None
            self.status = "DISCONNECTED"
            self.reconnect_result = f"FAILED: {e}"
            return False

    def _update_from_heartbeat(self, msg):
        try:
            mode_str = mavutil.mode_string_v10(msg)
        except Exception:
            mode_str = None
        self.flight_mode = mode_str if mode_str else f"UNKNOWN(custom_mode={msg.custom_mode})"
        self.armed = bool(msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED)
        self.last_heartbeat_time = time.time()

    def poll(self):
        """Non-blocking check for a fresh heartbeat / detect a dropped link.
        Call once per main loop iteration. Does not attempt reconnection itself."""
        if self.master is None:
            self.status = "DISCONNECTED"
            return

        try:
            msg = self.master.recv_match(type="HEARTBEAT", blocking=False)
            if msg is not None:
                self._update_from_heartbeat(msg)
                self.status = "CONNECTED"
        except Exception:
            # Serial port itself went away (unplugged, etc.)
            self.master = None
            self.status = "DISCONNECTED"
            return

        # Heartbeat timeout — link is open but Pixhawk has gone quiet
        if self.status == "CONNECTED" and (time.time() - self.last_heartbeat_time) > HEARTBEAT_TIMEOUT:
            self.status = "DISCONNECTED"

    def maybe_reconnect(self):
        """Attempt reconnection if disconnected and the cooldown has elapsed.
        Returns the reconnect result string, or None if no attempt was made."""
        if self.status == "CONNECTED":
            return None

        now = time.time()
        if now - self.last_reconnect_attempt < RECONNECT_INTERVAL:
            return None

        self.last_reconnect_attempt = now
        print("Pixhawk link lost — attempting reconnection...")
        success = self._connect()
        if success:
            print(f"Reconnection SUCCESS. Flight mode: {self.flight_mode}, Armed: {self.armed}")
        else:
            print(f"Reconnection FAILED: {self.reconnect_result}")
        return self.reconnect_result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    hw = initialize_sensor_hardware()
    pixhawk = PixhawkLink(PIXHAWK_CONNECTION_STRING, PIXHAWK_BAUD_RATE)

    if not os.path.isfile(CSV_FILENAME):
        with open(CSV_FILENAME, mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp", "front_distance_mm", "left_distance_mm",
                "right_distance_mm", "back_distance_mm", "sensor_overall_status",
                "decision", "image_filename", "sensor_error_status",
                "pixhawk_status", "flight_mode", "armed", "reconnect_result",
            ])

    print("Starting hardware integration test loop... (Press Ctrl+C to stop)")

    try:
        while True:
            current_time = time.strftime("%Y-%m-%d %H:%M:%S")
            dists = {'f': None, 'l': None, 'r': None, 'b': None}
            sensor_error_status = hw['status']

            if hw['front']:
                try:
                    dists['f'] = hw['front'].range
                except Exception:
                    sensor_error_status = "FRONT_SENSOR_ERROR"
            if hw['left']:
                try:
                    dists['l'] = hw['left'].range
                except Exception:
                    sensor_error_status = "LEFT_SENSOR_ERROR"
            if hw['right']:
                try:
                    dists['r'] = hw['right'].range
                except Exception:
                    sensor_error_status = "RIGHT_SENSOR_ERROR"
            if hw['back']:
                try:
                    dists['b'] = hw['back'].range
                except Exception:
                    sensor_error_status = "BACK_SENSOR_ERROR"

            f_stat = get_status(dists['f'])
            l_stat = get_status(dists['l'])
            r_stat = get_status(dists['r'])
            b_stat = get_status(dists['b'])
            overall_status, decision = determine_logic(f_stat, l_stat, r_stat, b_stat)

            # --- Pixhawk link check + reconnect (Task 12) ---
            pixhawk.poll()
            reconnect_result = None
            if pixhawk.status != "CONNECTED":
                reconnect_result = pixhawk.maybe_reconnect()
                # No movement commands while the link is down, regardless of
                # what the sensors say.
                decision = "HOLD / CONNECTION FAULT"

            # Camera trigger on WARNING/DANGER (independent of Pixhawk link state)
            image_filename = "N/A"
            if overall_status in ["WARNING", "DANGER"]:
                print(f"[{overall_status}] detected! Triggering camera...")
                image_filename = capture_image()
                if image_filename == "CAMERA_ERROR":
                    sensor_error_status = (
                        "CAMERA_ERROR" if sensor_error_status == "OK"
                        else sensor_error_status + " | CAMERA_ERROR"
                    )

            print(
                f"{current_time} | F:{dists['f']} L:{dists['l']} R:{dists['r']} B:{dists['b']} "
                f"| {decision} | SensorErr: {sensor_error_status} "
                f"| Pixhawk: {pixhawk.status} ({pixhawk.flight_mode}, armed={pixhawk.armed})"
            )

            with open(CSV_FILENAME, mode='a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    current_time,
                    dists['f'] if dists['f'] is not None else "ERROR",
                    dists['l'] if dists['l'] is not None else "ERROR",
                    dists['r'] if dists['r'] is not None else "ERROR",
                    dists['b'] if dists['b'] is not None else "ERROR",
                    overall_status,
                    decision,
                    image_filename,
                    sensor_error_status,
                    pixhawk.status,
                    pixhawk.flight_mode,
                    pixhawk.armed,
                    reconnect_result if reconnect_result is not None else "N/A",
                ])

            if "CRITICAL" not in sensor_error_status:
                hw['status'] = "OK"

            time.sleep(LOOP_DELAY)

    except KeyboardInterrupt:
        print("\nStopped by user.")
    finally:
        if pixhawk.master is not None:
            try:
                pixhawk.master.close()
            except Exception:
                pass


if __name__ == "__main__":
    main()