# Wiring Notes — Single VL53L0X to Raspberry Pi 4

## Purpose
Connect a single VL53L0X Time-of-Flight sensor to a Raspberry Pi 4 for baseline distance testing before scaling to multi-sensor setup.

---

## Setup Steps

### 1. OS & Tools
- OS: Raspberry Pi OS (64-bit) Lite
- Install Python and Git:
  ```bash
  sudo apt install -y python3 git
  ```
- Enable I2C:
  ```bash
  sudo raspi-config
  # Interface Options → I2C → Yes → Finish
  sudo reboot
  ```
- Update and install I2C tools:
  ```bash
  sudo apt update
  sudo apt install -y i2c-tools python3-smbus
  ```

### 2. Python Library
> `pip install adafruit-circuitpython-vl53l0x` requires a **virtual environment** due to conflict with `--on-package` flag.

```bash
python3 -m venv venv
source venv/bin/activate
pip install adafruit-circuitpython-vl53l0x
```

---

## Wiring — VL53L0X → Raspberry Pi 4

| VL53L0X Pin | RPi 4 Pin        | Notes            |
|-------------|------------------|------------------|
| VCC         | Pin 1 (3.3V)     |                  |
| GND         | Pin 6 (Ground)   |                  |
| SDA         | Pin 3 (GPIO 2)   | I2C Data         |
| SCL         | Pin 5 (GPIO 3)   | I2C Clock        |

---

## Testing

### Verify I2C detection
```bash
i2cdetect -y 1
# Expected: device at 0x29
```

### Single sensor live readings — `single_sensor_test.py`
- Import required libraries
- Initialize I2C bus and VL53L0X sensor
- Continuously fetch `sensor.range` (distance in mm)
- Print distance in **mm** and **cm**
- Loop until `Ctrl+C`

### CSV logger — `single_sensor_csv_logger.py`
- Import required libraries
- Initialize I2C bus and sensor
- Write CSV headers if file does not already exist
- Open in append mode if file exists
- Continuously write current **timestamp**, distance in **mm**, and distance in **cm**
- Loop until `Ctrl+C`

---

## Sensor Test Results

| Sensor   | Status  | Min Distance | Max Distance |
|----------|---------|-------------|-------------|
| Sensor 1 | Correct | ≈ 2 cm      | ≈ 819 cm    |
| Sensor 2 | Fault   | ≈ 5 cm      | ≈ 819 cm    |
| Sensor 3 | Fault   | ≈ 9 cm      | ≈ 819 cm    |
| Sensor 4 | Correct | ≈ 2 cm      | ≈ 819 cm    |

> Sensors 2 and 3 showed abnormal minimum distances — likely faulty units.

---

## Notes
- Default I2C address of VL53L0X is `0x29`
- All scripts run inside the virtual environment (`source venv/bin/activate`)
