# Drone 1 — Current Integration Status

_Milestone freeze snapshot — confirmed via live on-device run (Aug 5, 2026)._

---

## Completed Components

- Raspberry Pi 4 companion computer, OS installed and configured (I2C enabled, camera interface enabled)
- 4× VL53L0X ToF sensors wired through a TCA9548A I2C multiplexer (channels 0–3)
- TCA9548A SDA/SCL wiring bug (SDA↔SDO / SCL↔SCO swap) identified and fixed
- Pixhawk 2.4.8 connected to Pi over TELEM2 UART (`/dev/ttyAMA0`), TX/RX crossed, GND shared, VCC intentionally left disconnected
- MAVLink heartbeat confirmed live: System ID 1, Component ID 1, autopilot type 3 (ArduPilot), vehicle type 2 (quadrotor), flight mode STABILIZE, armed=False
- Obstacle-decision logic (SAFE/WARNING/DANGER thresholds + front/left/right/back priority rules) implemented and confirmed live — DANGER state correctly triggers STOP/HOLD decision
- CSV logging confirmed working (`robot_log.csv`, `sensor_readings.csv`, `hardware_integration_log.csv` all contain real logged rows)
- Camera image capture on WARNING/DANGER confirmed working — triggers correctly on each DANGER event during live run
- `camera_test.py` confirmed working via `rpicam-still`
- Pixhawk reconnect logic (Task 12) implemented in `hardware_integration_test.py` and running live — link stayed CONNECTED throughout this run, status correctly reported each loop
- ESC calibration issue resolved — no longer needs recalibration on every power cycle

## Working Scripts (confirmed via live re-run)

| Script | Status |
|---|---|
| `camera_test.py` | Working |
| `tca9548a_test.py` | Working — all 4 channels detected |
| `single_sensor_test.py` / `single_sensor_csv_logger.py` | Working |
| `sensor_camera_logger.py` | Working end-to-end |
| `obstacle_status.py` | Working — logic consistent with live run |
| `pixhawk_connection_test.py` | Confirmed working live — heartbeat received, flight mode decoded as STABILIZE, armed status correctly shown as False |
| `hardware_integration_test.py` | Confirmed working live — sensor + camera + Pixhawk integration ran continuously, DANGER detections logged correctly with CONNECTED Pixhawk status each cycle, no crashes |

## Sensors Installed

- Front (TCA channel 0)
- Left (TCA channel 1)
- Right (TCA channel 2)
- Back (TCA channel 3)

All four confirmed reporting live distance values (F/L/R/B all populated in console output and CSV).

## Sensors Not Installed

- None beyond the 4 currently wired (front/left/right/back).

## Current Wiring

- VL53L0X → TCA9548A: VIN→VIN, GND→GND, SDA→SDO, SCL→SCO (corrected mapping)
- TCA9548A → Pi 4: VIN→3.3V, GND→GND, SDA→GPIO2 (Pin 3), SCL→GPIO3 (Pin 5)
- Pixhawk TELEM2 → Pi UART: TX→Pi RX (GPIO15), RX→Pi TX (GPIO14), GND→Pi GND, VCC not connected
- Camera: connected via CSI, confirmed working

## Current Software Problems

- None outstanding — flight mode decoding, armed/disarmed status, and reconnect behavior are all implemented and confirmed working live.

## Current Hardware Problems

- None outstanding — ESC calibration issue (previously required recalibration on every power-up, causing a stuck loop) has been fixed.

## Remaining Work

- Finalize drone-1 mounting and run endurance test