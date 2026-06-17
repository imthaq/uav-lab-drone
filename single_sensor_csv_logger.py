import time
import csv
import os
import board
import busio
import adafruit_vl53l0x
from datetime import datetime

i2c= busio.I2C(board.SCL, board.SDA)
sensor= adafruit_vl53l0x.VL53L0X(i2c)

csv_filename= "sensor_readings.csv"

if not os.path.exists(csv_filename):
    with open(csv_filename, mode='w', newline='') as file:
        writer= csv.writer(file)
        writer.writerow(["Timestamp", "Distance_mm", "Distance_cm"])
print(f"Logging data to {csv_filename}... Press Ctrl+C to stop.")

try:
    with open(csv_filename, mode='a', newline='') as file:
        writer=csv.writer(file)
        while True:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            distance_mm=sensor.range
            distance_cm=distance_mm/10.0
            
            writer.writerow([current_time, distance_mm, distance_cm])
            file.flush()

            print(f"[{current_time}] Saved: {distance_cm} cm")
            time.sleep(1.0)

except KeyboardInterrupt:
    print("\nLogging stopped. File saved successfully")

