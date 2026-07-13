import time
import board
import busio
import csv
import subprocess
import os
import adafruit_tca9548a
import adafruit_vl53l0x

# Configuration
SAFE_THRESHOLD = 700
DANGER_THRESHOLD = 300
CSV_FILENAME = "robot_log.csv"
IMAGE_DIR = "captures"

# Ensure image directory exists
os.makedirs(IMAGE_DIR, exist_ok=True)

def initialize_hardware():
    """Setup I2C, Multiplexer, and Sensors."""
    hw = {'i2c': None, 'tca': None, 'front': None, 'left': None, 'right': None, 'back': None, 'status': "OK"}
    try:
        hw['i2c'] = busio.I2C(board.SCL, board.SDA)
        hw['tca'] = adafruit_tca9548a.TCA9548A(hw['i2c'])
        
        # Wrapping individual sensors in try-except to not fail entirely if one drops
        try: hw['front'] = adafruit_vl53l0x.VL53L0X(hw['tca'][0])
        except Exception: hw['status'] = "FRONT_SENSOR_ERROR"
            
        try: hw['left'] = adafruit_vl53l0x.VL53L0X(hw['tca'][1])
        except Exception: hw['status'] = "LEFT_SENSOR_ERROR"
            
        try: hw['right'] = adafruit_vl53l0x.VL53L0X(hw['tca'][2])
        except Exception: hw['status'] = "RIGHT_SENSOR_ERROR"

        try: hw['back'] = adafruit_vl53l0x.VL53L0X(hw['tca'][3])
        except Exception: hw['status'] = "BACK_SENSOR_ERROR"

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
    
    # Calculate overall status (highest severity)
    if "DANGER" in statuses: overall = "DANGER"
    elif "WARNING" in statuses: overall = "WARNING"
    elif "ERROR" in statuses: overall = "ERROR"
    else: overall = "SAFE"

    # Decisions
    if danger_count > 1 or f_stat == "DANGER": decision = "STOP / HOLD"
    elif l_stat == "DANGER": decision = "MOVE RIGHT"
    elif r_stat == "DANGER": decision = "MOVE LEFT"
    elif b_stat == "DANGER": decision = "HOLD POSITION (NO REVERSE)"
    elif f_stat == "WARNING": decision = "SLOW / CAUTION"
    elif l_stat == "WARNING": decision = "SLIGHT RIGHT CORRECTION"
    elif r_stat == "WARNING": decision = "SLIGHT LEFT CORRECTION"
    elif b_stat == "WARNING": decision = "CAUTION REVERSE"
    elif overall == "SAFE": decision = "MOVE FORWARD"
    else: decision = "UNKNOWN"

    return overall, decision

def capture_image():
    """Captures an image and returns the filename. Returns 'CAMERA_ERROR' if failed."""
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    filename = f"{IMAGE_DIR}/alert_{timestamp}.jpg"
    
    try:
        # Updated to use rpicam-still and added --vflip
        result = subprocess.run(
            ["rpicam-still", "-o", filename, "--nopreview", "-t", "500", "--vflip"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            return filename
        else:
            print(f"CAMERA_ERROR details: {result.stderr.strip()}")
            return "CAMERA_ERROR"
    except FileNotFoundError:
        return "CAMERA_ERROR (Command not found)"
    except Exception as e:
        print(f"CAMERA_ERROR: {e}")
        return "CAMERA_ERROR"

def main():
    hw = initialize_hardware()
    
    # Write CSV Header if file doesn't exist
    if not os.path.isfile(CSV_FILENAME):
        with open(CSV_FILENAME, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["timestamp", "front_distance_mm", "left_distance_mm", 
                             "right_distance_mm", "back_distance_mm", "overall_status", "decision", 
                             "image_filename", "error_status"])

    print("Starting Main Logger Loop... (Press Ctrl+C to stop)")
    
    try:
        while True:
            current_time = time.strftime("%Y-%m-%d %H:%M:%S")
            dists = {'f': None, 'l': None, 'r': None, 'b': None}
            error_status = hw['status']

            # Read Front
            if hw['front']:
                try: dists['f'] = hw['front'].range
                except Exception: error_status = "FRONT_SENSOR_ERROR"
            
            # Read Left
            if hw['left']:
                try: dists['l'] = hw['left'].range
                except Exception: error_status = "LEFT_SENSOR_ERROR"
                
            # Read Right
            if hw['right']:
                try: dists['r'] = hw['right'].range
                except Exception: error_status = "RIGHT_SENSOR_ERROR"

            # Read Back
            if hw['back']:
                try: dists['b'] = hw['back'].range
                except Exception: error_status = "BACK_SENSOR_ERROR"

            f_stat = get_status(dists['f'])
            l_stat = get_status(dists['l'])
            r_stat = get_status(dists['r'])
            b_stat = get_status(dists['b'])

            overall_status, decision = determine_logic(f_stat, l_stat, r_stat, b_stat)

            # Camera Trigger Logic
            image_filename = "N/A"
            if overall_status in ["WARNING", "DANGER"]:
                print(f"[{overall_status}] detected! Triggering camera...")
                image_filename = capture_image()
                if image_filename == "CAMERA_ERROR":
                    error_status = "CAMERA_ERROR" if error_status == "OK" else error_status + " | CAMERA_ERROR"

            # Print to console
            print(f"{current_time} | F:{dists['f']} L:{dists['l']} R:{dists['r']} B:{dists['b']} | {decision} | Error: {error_status}")

            # Log to CSV
            with open(CSV_FILENAME, mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([
                    current_time, 
                    dists['f'] if dists['f'] is not None else "ERROR",
                    dists['l'] if dists['l'] is not None else "ERROR",
                    dists['r'] if dists['r'] is not None else "ERROR",
                    dists['b'] if dists['b'] is not None else "ERROR",
                    overall_status, 
                    decision, 
                    image_filename, 
                    error_status
                ])
            
            # Reset error status for next loop unless it's a critical I2C crash
            if "CRITICAL" not in error_status:
                hw['status'] = "OK"

            # Brief pause to prevent flooding the I2C bus and generating massive CSVs
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\nLogging stopped by user.")

if __name__ == "__main__":
    main()
