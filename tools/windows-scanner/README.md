# Cachito BLE scanner v6

This is the current stable Windows scanner snapshot. It is a diagnostic/capture tool, not a controller.

## Run

1. Install Python 3, tkinter, and `bleak`.
2. Keep all files in one folder.
3. Double-click `start_cachito.cmd`.
4. Use `diagnostic.cmd` when a console window must remain visible.

Both `.cmd` files are intentionally English ASCII and contain no BOM.

## Sampling rule

The official app uses continuous 0-100 sliders. Each guided step has two phases:

1. PREPARE: adjust the slider or phone pose; no capture label is written.
2. CAPTURE: click `已调好，开始采样`; the scanner clears its dedup cache and records only the marked window.

- Static state: 6 seconds.
- Dynamic flat → vertical → flat movement: 12 seconds.
- Only packets between `CAPTURE START` and `CAPTURE END` belong to the labeled target.

## Scope

The tool:

- scans BLE advertisements;
- records address, RSSI, local name, service UUIDs, manufacturer data, and service data;
- provides voice/countdown guidance for reproducible observation.

The tool does not:

- connect to the accessory;
- advertise BLE packets;
- send GATT writes;
- control the device;
- prove whether the observed advertiser is the phone or accessory.
