import subprocess
import signal
import sys
import time
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

camera_process = None

def start_camera():
    global camera_process
    print(f"[{datetime.now()}] Starting camera...")
    camera_process = subprocess.Popen(
        CAMERA_CMD,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

def stop_camera():
    global camera_process
    if camera_process and camera_process.poll() is None:
        print(f"[{datetime.now()}] Stopping camera...")
        camera_process.terminate()   # graceful shutdown, like Ctrl+C
        camera_process.wait()
        print("Camera stopped, file saved.")

def handle_exit(sig, frame):
    """Catch Ctrl+C so the video file closes properly."""
    stop_camera()
    sys.exit(0)

signal.signal(signal.SIGINT, handle_exit)


# Thresholds
SAFE_THRESHOLD = 700
DANGER_THRESHOLD = 300
def get_status(distance):
    """Convert distance to status level."""
    if distance is None:
        return "ERROR"
    if distance > SAFE_THRESHOLD:
        return "SAFE"
    elif DANGER_THRESHOLD <= distance <= SAFE_THRESHOLD:
        return "WARNING"
    else:
        return "DANGER"
def determine_decision(front_stat, left_stat, right_stat, back_stat):
    """Determine movement decision based on priority logic."""
    statuses = [front_stat, left_stat, right_stat, back_stat]
    danger_count = statuses.count("DANGER")
    
    # Priority 1: Multiple Dangers or Front Danger
    if danger_count > 1 or front_stat == "DANGER":
        return "STOP / HOLD"
    
    # Priority 2: Side Dangers
    if left_stat == "DANGER":
        return "MOVE RIGHT"
    if right_stat == "DANGER":
        return "MOVE LEFT"

    # Priority 2b: Back Danger (can't reverse)
    if back_stat == "DANGER":
        return "HOLD POSITION (NO REVERSE)"
        
    # Priority 3: Warnings
    if front_stat == "WARNING":
        return "SLOW / CAUTION"
    if left_stat == "WARNING":
        return "SLIGHT RIGHT CORRECTION"
    if right_stat == "WARNING":
        return "SLIGHT LEFT CORRECTION"
    if back_stat == "WARNING":
        return "CAUTION REVERSE"
        
    # Priority 4: All Safe
    if all(s == "SAFE" for s in statuses):
        return "MOVE FORWARD"
        
    return "UNKNOWN"

# --- Main program ---
def main():
    start_camera()
    i2c = busio.I2C(board.SCL, board.SDA)
    tca = adafruit_tca9548a.TCA9548A(i2c)
    
    sensors = {}
    counter = 0
    try:
        while True:
            # This is where your own logic runs *while* the camera records
            # Initialize sensors (Assuming Front=0, Left=1, Right=2, Back=3)
            try:
               sensors['front'] = adafruit_vl53l0x.VL53L0X(tca[0])
               sensors['left'] = adafruit_vl53l0x.VL53L0X(tca[1])
               sensors['right'] = adafruit_vl53l0x.VL53L0X(tca[2])
               sensors['back'] = adafruit_vl53l0x.VL53L0X(tca[3])
               print("All sensors initialized.")
            except Exception as e:
               print(f"SENSOR_ERROR during initialization: {e}")
               return
            print("Starting sensor read loop... (Press Ctrl+C to stop)")
            try:
             while True:
               # Read distances
           
              f_dist = sensors['front'].range
              l_dist = sensors['left'].range
              r_dist = sensors['right'].range
              b_dist = sensors['back'].range
            
              # Get statuses
              f_stat = get_status(f_dist)
              l_stat = get_status(l_dist)
              r_stat = get_status(r_dist)
              b_stat = get_status(b_dist)
            
              # Get decision
              decision = determine_decision(f_stat, l_stat, r_stat, b_stat)
            
              print(f"F:{f_dist}mm({f_stat}) | L:{l_dist}mm({l_stat}) | R:{r_dist}mm({r_stat}) | B:{b_dist}mm({b_stat}) -> DECISION: {decision}")
              time.sleep(0.5)
            
            except KeyboardInterrupt:
              print("\nExiting obstacle_status.py")
              counter += 1
            # Example: check if the camera process died unexpectedly
            if camera_process.poll() is not None:
                print("Camera process exited unexpectedly!")
                break

            # Example: stop automatically after 60 seconds
            if counter >= 60:
                print("Reached time limit, stopping recording.")
                break

            time.sleep(1)
    finally:
        stop_camera()

if __name__ == "__main__":
    main()
