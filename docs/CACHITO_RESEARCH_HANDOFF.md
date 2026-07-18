# Cachito research handoff - 2026-07-19

## 1. Goal and boundaries

Goal: identify the shortest reliable way to control a Cachito accessory from an AI-accessible program.

Desired later behavior, not yet implemented:

- suction channel: pause/0 plus apparent 1-100 UI slider;
- piston channel: pause/0 plus apparent 1-100 UI slider;
- “嗨翻” means gravity/tilt control;
- voice, countdown, and action logs are later layers.

Current phase is transport/protocol identification only. Do not create v7, rewrite the working scanner, or send unverified nonzero commands.

## 2. Windows environment and startup diagnosis

Verified manually:

- Python `C:\Python314\python.exe`, version 3.14.4, 64-bit;
- pip 26.1.1;
- tkinter 8.6;
- bleak imports correctly;
- minimal Tkinter GUI works;
- minimal `BleakScanner.discover(timeout=8.0)` works;
- minimal Tkinter plus background BLE scan works.

The original v6 startup failure was caused by the launcher layer, not by Python/Tkinter/Bleak. The old `.cmd` files used UTF-8 BOM and Chinese command text, which could become garbled under `cmd.exe` before Python started.

Encoding rules fixed for future work:

- `.ps1`: UTF-8 with BOM for Windows PowerShell 5.1 compatibility;
- `.py`, `.json`, `.md`: UTF-8 without BOM;
- `.bat`/`.cmd`: English ASCII only, UTF-8 without BOM, launcher logic only;
- do not change system locale, registry, or global code page to hide encoding faults.

## 3. Scanner data-quality fix

The first guided scanner mislabeled intermediate values because it started capture immediately after displaying a target. The control is a continuous slider, so moving from one target to another produces many intermediate broadcasts.

The corrected v6 state machine is:

1. PREPARE: user adjusts slider/phone pose; no capture label is written.
2. User clicks “已调好，开始采样”.
3. CAPTURE: clear dedup cache, write `CAPTURE START`, collect for 6 seconds (12 seconds for dynamic movement), then write `CAPTURE END`.
4. Advance to the next PREPARE step.

The clean run completed all 21 captures.

## 4. BLE observations

Two runs showed a strong advertiser carrying packets correlated with Cachito actions:

- first run: `55:32:AC:CE:F6:8B`;
- clean run: `7D:C2:DC:2A:3E:B6`.

The address changed between runs but stayed stable during each run. This is consistent with a private/random BLE address, but does not identify whether the advertiser is the phone or the accessory.

Repeated packet structure:

- Service UUID prefix: `710002..`;
- stable middle: `0400-265d`;
- `0302` correlates with suction;
- `050a` correlates with piston;
- an earlier run showed `0601` when gravity mode was enabled;
- Apple manufacturer company ID `0x004C` repeatedly appeared with payload `0100000000000000000000020000000000`.

Example at the user-labeled 100 suction position:

`71000247-0400-265d-0302-6400000000aa`

Working interpretation only:

- `0302` is a suction channel/mode field;
- the first byte of the final group is correlated with the value (`64` hex = 100);
- the first group’s final byte and final group’s last byte change and may be sequence/checksum/derived fields.

## 5. Clean static samples

These are observations, not a validated UI-to-protocol table. Slider targets were user-selected, and the 1/return-to-zero samples disagree.

| UI target | suction byte | piston byte |
|---|---:|---:|
| baseline/0 | `00` | not isolated |
| 1 | `00` ambiguous | `01` |
| 10 | `20` | `20` |
| 25 | `2B` | `2B` |
| 50 | `3E` | `3E` |
| 75 | `51` | `51` |
| 100 | `64` | `64` |
| return to 0 | `00` | `01` ambiguous |

The middle points look regular, but no formula should be shipped from these approximate slider positions. Exact UI numeric values were not independently verified.

## 6. Critical identity question

The strongest current hypothesis is that `710002..` may be emitted by the iPhone app rather than by the accessory:

- manufacturer company ID is Apple `0x004C`;
- prior app inspection showed both `bluetooth-central` and `bluetooth-peripheral` background modes;
- prior symbol inspection found `CBPeripheralManager` and `startAdvertisingWithServiceUUID:`-style symbols;
- packets change exactly when app sliders or gravity mode change.

If true, connecting to the random address with `BleakClient` is the wrong goal. It may be a temporary phone advertisement while the accessory scans those advertisements.

This remains unverified.

## 7. Prior iOS/macOS observations requiring re-verification

Previously observed:

- bundle: `/Applications/Cachito.app/Wrapper/CachitoiOS.app`;
- executable: `CachitoiOS`;
- architecture: arm64;
- symbols/strings included `BleManager`, `AdvertisHelper`, `ToyCommondModel`, `UserRemoteCommandModel`, `CustomModePlayManager`, `BTModeData`, `OOMWritenHandler`, `CBPeripheralManager`, `startAdvertisingWithServiceUUID:`, `ZJQserviceUUID:`, `writeValue:forCharacteristic:type:`, and `dataOutCharacteristic`.

These clues suggest both advertisement-based control and GATT writes may exist. The original extraction files are not available in this runtime, so Claude must not treat this list as canonical without checking the binary.

## 8. Official remote path confirmed

The official app provides:

- “发起远程” on the host phone;
- “远程控制” on a second phone;
- a temporary six-character invitation code;
- a successful end-to-end control test.

The test code is intentionally omitted as an ephemeral credential.

Likely architecture:

`accessory <-BLE-> host app <-cloud session-> remote app`

The six-character code may only be a lookup key; server URL, session token, heartbeat, and transport can remain internal to the app.

## 9. Candidate routes

### A. Document and emulate the official remote-controller flow

Preferred if the client/server flow is observable and stable. The host app continues handling BLE pairing and random addresses. Needed evidence: session creation, code exchange, transport type, message schema, authentication, expiry, heartbeat, and reconnect behavior.

### B. Reproduce the app’s BLE advertisements

Plausible if the phone is the `710002..` advertiser. Windows/Bleak is mainly a central/client stack and may not be suitable for peripheral advertising. macOS CoreBluetooth, Linux BlueZ, ESP32, or nRF52 may be required. Timing, sequence/checksum, and association logic remain unknown.

### C. Connect directly to the accessory over GATT

Plausible because app symbols mention characteristic writes. First find the accessory’s own advertisement while the official app is disconnected, then perform read-only service/characteristic enumeration using the scanned `BLEDevice` object. Do not assume the `710002..` advertiser is connectable.

### D. Automate the official UI

Lowest protocol risk but fragile, difficult to run headlessly, and poor as a long-term AI integration. Keep only as fallback.

## 10. Recommended next decision test

First establish who emits `710002..` without writing anything:

1. app killed, accessory on;
2. app open, accessory off;
3. app open, accessory on;
4. compare presence, RSSI, address, and packet behavior.

In parallel, document one official remote session’s ordinary client/server flow without publishing codes or credentials.

Decision:

- readable/stable remote flow -> Route A;
- phone advertisement confirmed and remote flow opaque -> Route B;
- separate connectable accessory plus writable GATT service found -> Route C;
- otherwise temporary Route D.

## 11. Safety and exclusions

- Do not hard-code either observed address.
- “Seen in scan” does not mean “connectable”.
- Do not ship a value formula from six approximate positions.
- Begin with read-only enumeration and pause/zero tests.
- Prefer unloaded bench testing and keep physical power-off available.
- Rate-limit experiments and log timestamp, transport, session/address, command, and result.
- Do not publish invitation codes, tokens, or account credentials.

## 12. Files actually included in this PR

- `README.md`;
- this complete handoff;
- `docs/CLAUDE_REVIEW_PROMPT.md`;
- `analysis/static_samples.csv`;
- `documents/REUPLOAD_REQUIRED.md`.

The original scanner archives, full raw logs, screenshot, and previously shared Word/PDF originals are not attached to this PR. A complete local evidence bundle was prepared separately, but the inaccessible prior documents are not reconstructed or represented as originals.
