import subprocess
import signal
import sys
import time
import os
from datetime import datetime
import board
import busio
import adafruit_tca9548a
import adafruit_vl53l0x

# --- Configuration ---
OUTPUT_PATH = "udp://172.17.23.137:5000"
CAMERA_CMD = [
    "rpicam-vid", "-t", "0", "--inline", "--vflip",
    "--width", "640", "--height", "480",
    "-o", OUTPUT_PATH
]

IMAGE_DIR = "captures/"
CAPTURE_COOLDOWN = 3  # seconds between captures, to avoid spamming

camera_process = None
last_capture_time = 0

def start_camera():
    global camera_process
    print(f"[{datetime.now()}] Starting camera stream...")
    camera_process = subprocess.Popen(
        CAMERA_CMD,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

def stop_camera():
    global camera_process
    if camera_process and camera_process.poll() is None:
        print(f"[{datetime.now()}] Stopping camera...")
        camera_process.terminate()
        camera_process.wait()
        print("Camera stopped.")

def capture_image(reason="DANGER"):
    """Take a still snapshot using rpicam-still, saved with a timestamp."""
    global last_capture_time
    now = time.time()
    if now - last_capture_time < CAPTURE_COOLDOWN:
        return  # skip, still in cooldown
    last_capture_time = now

    os.makedirs(IMAGE_DIR, exist_ok=True)
    filename = os.path.join(
        IMAGE_DIR,
        f"{reason}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    )

    still_cmd = [
        "rpicam-still",
        "-t", "1",            # minimal delay, capture immediately
        "--vflip",
        "--width", "640",
        "--height", "480",
        "-n",                 # no preview window
        "-o", filename
    ]

    try:
        subprocess.Popen(
            still_cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print(f"[{datetime.now()}] DANGER detected -> capturing image: {filename}")
    except Exception as e:
        print(f"Failed to capture image: {e}")

def handle_exit(sig, frame):
    """Catch Ctrl+C so the video file closes properly."""
    stop_camera()
    sys.exit(0)

signal.signal(signal.SIGINT, handle_exit)

# Thresholds
SAFE_THRESHOLD = 700
DANGER_THRESHOLD = 300

def get_status(distance):
    if distance is None:
        return "ERROR"
    if distance > SAFE_THRESHOLD:
        return "SAFE"
    elif DANGER_THRESHOLD <= distance <= SAFE_THRESHOLD:
        return "WARNING"
    else:
        return "DANGER"

def determine_decision(front_stat, left_stat, right_stat, back_stat):
    statuses = [front_stat, left_stat, right_stat, back_stat]
    danger_count = statuses.count("DANGER")

    if danger_count > 1 or front_stat == "DANGER":
        return "STOP / HOLD"
    if left_stat == "DANGER":
        return "MOVE RIGHT"
    if right_stat == "DANGER":
        return "MOVE LEFT"
    if back_stat == "DANGER":
        return "HOLD POSITION (NO REVERSE)"
    if front_stat == "WARNING":
        return "SLOW / CAUTION"
    if left_stat == "WARNING":
        return "SLIGHT RIGHT CORRECTION"
    if right_stat == "WARNING":
        return "SLIGHT LEFT CORRECTION"
    if back_stat == "WARNING":
        return "CAUTION REVERSE"
    if all(s == "SAFE" for s in statuses):
        return "MOVE FORWARD"
    return "UNKNOWN"

def safe_read(sensor):
    """Read a sensor's range safely, returning None on I2C failure."""
    try:
        return sensor.range
    except OSError as e:
        print(f"I2C read error: {e}")
        return None

# --- Main program ---
def main():
    # start_camera()
    i2c = busio.I2C(board.SCL, board.SDA)
    tca = adafruit_tca9548a.TCA9548A(i2c)

    try:
        sensors = {
            'front': adafruit_vl53l0x.VL53L0X(tca[0]),
            'left':  adafruit_vl53l0x.VL53L0X(tca[1]),
            'right': adafruit_vl53l0x.VL53L0X(tca[2]),
            'back':  adafruit_vl53l0x.VL53L0X(tca[3]),
        }
        print("All sensors initialized.")
    except Exception as e:
        print(f"SENSOR_ERROR during initialization: {e}")
        stop_camera()
        return

    print("Starting sensor read loop... (Press Ctrl+C to stop)")

    try:
        while True:
            f_dist = safe_read(sensors['front'])
            l_dist = safe_read(sensors['left'])
            r_dist = safe_read(sensors['right'])
            b_dist = safe_read(sensors['back'])

            f_stat = get_status(f_dist)
            l_stat = get_status(l_dist)
            r_stat = get_status(r_dist)
            b_stat = get_status(b_dist)

            decision = determine_decision(f_stat, l_stat, r_stat, b_stat)

            print(f"F:{f_dist}mm({f_stat}) | L:{l_dist}mm({l_stat}) | "
                  f"R:{r_dist}mm({r_stat}) | B:{b_dist}mm({b_stat}) -> DECISION: {decision}")

            # --- Trigger image capture on any DANGER ---
            if "DANGER" in (f_stat, l_stat, r_stat, b_stat):
                capture_image(reason="DANGER")

            if camera_process.poll() is not None:
                print("Camera process exited unexpectedly!")
                break

            time.sleep(0.5)

    finally:
        stop_camera()

if __name__ == "__main__":
    main()
