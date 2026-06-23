import time
import board
import busio
import adafruit_tca9548a
import adafruit_vl53l0x

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

def determine_decision(front_stat, left_stat, right_stat):
    """Determine movement decision based on priority logic."""
    statuses = [front_stat, left_stat, right_stat]
    danger_count = statuses.count("DANGER")
    
    # Priority 1: Multiple Dangers or Front Danger
    if danger_count > 1 or front_stat == "DANGER":
        return "STOP / HOLD"
    
    # Priority 2: Side Dangers
    if left_stat == "DANGER":
        return "MOVE RIGHT"
    if right_stat == "DANGER":
        return "MOVE LEFT"
        
    # Priority 3: Warnings
    if front_stat == "WARNING":
        return "SLOW / CAUTION"
    if left_stat == "WARNING":
        return "SLIGHT RIGHT CORRECTION"
    if right_stat == "WARNING":
        return "SLIGHT LEFT CORRECTION"
        
    # Priority 4: All Safe
    if all(s == "SAFE" for s in statuses):
        return "MOVE FORWARD"
        
    return "UNKNOWN"

def main():
    i2c = busio.I2C(board.SCL, board.SDA)
    tca = adafruit_tca9548a.TCA9548A(i2c)
    
    sensors = {}
    # Initialize sensors (Assuming Front=0, Left=1, Right=2)
    try:
        sensors['front'] = adafruit_vl53l0x.VL53L0X(tca[0])
        sensors['left'] = adafruit_vl53l0x.VL53L0X(tca[1])
        sensors['right'] = adafruit_vl53l0x.VL53L0X(tca[2])
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
            
            # Get statuses
            f_stat = get_status(f_dist)
            l_stat = get_status(l_dist)
            r_stat = get_status(r_dist)
            
            # Get decision
            decision = determine_decision(f_stat, l_stat, r_stat)
            
            print(f"F:{f_dist}mm({f_stat}) | L:{l_dist}mm({l_stat}) | R:{r_dist}mm({r_stat}) -> DECISION: {decision}")
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("\nExiting obstacle_status.py")

if __name__ == "__main__":
    main()