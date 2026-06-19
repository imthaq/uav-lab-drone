# Wiring Notes — 4× VL53L0X via TCA9548A MUX to Raspberry Pi 4

## Purpose
Connect 4 VL53L0X sensors (all sharing default I2C address `0x29`) to a Raspberry Pi 4 using a TCA9548A 1-to-8 I2C multiplexer on channels 0–3.

---

## Hardware

| Component  | Quantity |
|------------|----------|
| Raspberry Pi 4 | 1 |
| TCA9548A I2C MUX (3–8 MUX) | 1 |
| VL53L0X ToF Sensor | 4 |

---

## Wiring — TCA9548A → Raspberry Pi 4

| TCA9548A Pin | RPi 4 Pin        | Notes          |
|--------------|------------------|----------------|
| VIN          | 3.3V             |                |
| GND          | Ground           |                |
| SDA          | Pin 3 (GPIO 2)   | I2C Data       |
| SCL          | Pin 5 (GPIO 3)   | I2C Clock      |

---

## Wiring — VL53L0X → TCA9548A (per sensor, channels 0–3)

| VL53L0X Pin | TCA9548A Pin |
|-------------|--------------|
| VIN         | VIN          |
| GND         | GND          |
| SCL         | SDO (⚠ Error) |
| SDA         | SCO (⚠ Error) |

> ⚠ **Critical Fix:** Initial wiring used SDA→SDO / SCL→SCO (incorrect).  
> Correct mapping is **SDA→SDO** and **SCL→SCO** as labeled on the TCA9548A channel headers.  
> Error before fix: `No I2C device at 0x29`

Each of the 4 sensors connects identically to its own TCA channel (CH0 through CH3).

---

## Channel Assignment

| TCA Channel | Sensor   |
|-------------|----------|
| CH0         | Sensor 1 |
| CH1         | Sensor 2 |
| CH2         | Sensor 3 |
| CH3         | Sensor 4 |

---

## Setup & Debugging

### Test script — `TCA9548A_test.py`
```bash
nano TCA9548A_test.py
```
- Insert I2C device scan code that iterates through TCA channels
- Switch TCA channel, then scan for VL53L0X at `0x29`
- Expected output: MUX detected, VL53L0X found per channel

### Common Error & Fix

| Error | Cause | Fix |
|-------|-------|-----|
| `No I2C device at 0x29` | SDA/SCL swapped on TCA channel headers | Swap: SDA→SDO, SCL→SCO |
| MUX detected but VL53L0X not found | Same swap issue | Same fix |

---

## Verification

- MUX (TCA9548A) verified present on I2C bus
- All 4 VL53L0X sensors connected to TCA channels 0–3
- All 8 TCA channels verified working correctly
- Code pushed to GitHub

---

## GitHub Notes

- **Issue:** `git push` asking for password (PAT not configured)
- **Fix:** Go to GitHub → Developer Settings → Personal Access Tokens → Generate token → use as password during push

---

## Notes
- TCA9548A default I2C address: `0x70`
- VL53L0X default I2C address: `0x29` (same for all — MUX required)
- All sensors share VIN/GND from TCA; only SCL/SDA are channel-switched
- Virtual environment must be active for `adafruit-circuitpython-vl53l0x`
