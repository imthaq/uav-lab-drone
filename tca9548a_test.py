import board
import busio
import adafruit_vl53l0x
import adafruit_tca9548a
import time



i2c = busio.I2C(board.SCL , board.SDA)
mux =  adafruit_tca9548a.TCA9548A(i2c)
sensor_ch0 = adafruit_vl53l0x.VL53L0X(mux[0])
sensor_ch1 = adafruit_vl53l0x.VL53L0X(mux[1])
sensor_ch2 = adafruit_vl53l0x.VL53L0X(mux[2])
sensor_ch3 = adafruit_vl53l0x.VL53L0X(mux[3])


sensors =  [sensor_ch0 , sensor_ch1 , sensor_ch2 , sensor_ch3]
print("Starting sensor readings... ")

try:
    while True:
        for st in range (0 ,  4 , 1):
        	print(f"\nChannel {st} distance: {sensors[st].range / 10} cm\n")
        time.sleep(4)
except KeyboardInterrupt:
    print("Program stopped by user")
