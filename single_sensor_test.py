import time
import board
import busio
import adafruit_vl53l0x

i2c= busio.I2C(board.SCL, board.SDA)
sensor=adafruit_vl53l0x.VL53L0X(i2c)

print(f"Testing VL53L0X sensor ... press Ctrl+C to stop")

try:
    while True:
        distance_mm=sensor.range
        print(f"Distance: {distance_mm} mm ({distance_mm/10:.1f} cm)")
        time.sleep(0.5)
except KeyboardInterrupt:
    print("\nTest stopped by user.")
