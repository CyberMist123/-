# Cachito research handoff - 2026-07-19

## 1. Goal

Determine the shortest reliable way to control a Cachito device from an AI-accessible program, preferably without depending on manual operation in the official app.

Desired final behavior, not yet implemented:

- two controllable channels: suction and piston;
- each channel has pause/zero and an apparent 1-100 UI slider;
- “嗨翻” is gravity/tilt control;
- later layers may add voice, countdown, and action logging;
- current phase is protocol identification and stable startup only.

## 2. Hard constraints from the debugging session

- Do not create a v7 or rewrite the project while the protocol is still uncertain.
- Separate environment, GUI, BLE scanning, and protocol questions.
- Do not guess an error before reproducing it.
- Windows PowerShell may be 5.1.
- `.ps1`: UTF-8 with BOM.
- `.py`, `.json`, `.md`: UTF-8 without BOM.
- `.bat`/`.cmd`: English ASCII only, UTF-8 without BOM; launcher only.
- Do not alter the system locale, registry, or global code page to hide encoding bugs.

## 3. Environment verified on Windows

Verified manually:

- Python: `C:\Python314\python.exe`, Python 3.14.4, 64-bit.
- pip: 26.1.1.
- tkinter: 8.6.
- bleak import succeeds.
- minimal Tkinter window opens and closes normally.
- minimal `BleakScanner.discover(timeout=8.0)` works and found ten devices.
- a minimal Tkinter + background Bleak scan also opened and closed normally.

Therefore the original startup failure was not evidence that Python, tkinter, bleak, threads, or asyncio were fundamentally broken.

## 4. Windows launcher bug and current scanner

The original v6 launchers were UTF-8 with BOM and contained Chinese command text. Under `cmd.exe` they could become garbled and fail before Python started.

The current launcher fix is intentionally small:

- ASCII-only `.cmd` files;
- no BOM;
- `cd /d "%~dp0"`;
- `py -3 -u "%~dp0cachito_scan_gui_v6.py"`;
- preserve exit code and pause so errors remain visible.

The current scanner also fixes a data-quality flaw. A continuous slider cannot be sampled by starting a timer as soon as a target is displayed, because all intermediate slider positions are then mislabeled as the target. The new state machine is:

1. PREPARE - user adjusts the slider or phone pose without a capture label.
2. User clicks “已调好，开始采样”.
3. CAPTURE - clear dedup cache, write `CAPTURE START`, collect for 6 seconds (12 seconds for dynamic movement), write `CAPTURE END`.
4. Advance to the next PREPARE step.

The clean run completed all 21 captures.

## 5. BLE observations

### 5.1 Candidate command broadcaster

Two different runs showed a strong nearby advertiser carrying the Cachito-correlated packets:

- first run candidate address: `55:32:AC:CE:F6:8B`;
- clean run candidate address: `7D:C2:DC:2A:3E:B6`.

The address changed between runs but stayed stable during each run. That is consistent with a private/random BLE address, but it does not prove whether the advertiser is the toy or the iPhone app.

The repeated packet family has:

- Service UUID prefix `710002..`;
- fixed UUID middle `0400-265d`;
- mode field `0302` or `050a` in most packets;
- Apple manufacturer company ID `0x004C` with recurring payload `0100000000000000000000020000000000`.

### 5.2 Correlated channel fields

Strong correlation in both runs:

- `0302` changes with suction operations;
- `050a` changes with piston operations;
- earlier capture showed a `0601` packet when gravity mode was enabled;
- with gravity mode active, packets alternate rapidly between `0302` and `050a`, and the first byte of the final UUID group changes with phone pose.

### 5.3 Static sample values from the clean run

These are observations, not a validated protocol table. The app uses continuous sliders, the target labels were user-selected positions, and some “1”/return-to-zero samples disagree.

| UI label | Suction observed byte | Piston observed byte |
|---|---:|---:|
| baseline/0 | `00` | not isolated in baseline |
| 1 | `00` (ambiguous) | `01` |
| 10 | `20` | `20` |
| 25 | `2B` | `2B` |
| 50 | `3E` | `3E` |
| 75 | `51` | `51` |
| 100 | `64` | `64` |
| return to 0 | `00` | `01` (ambiguous) |

The middle points form a suspiciously regular sequence, but no formula should be hard-coded yet. The clean dataset still describes slider target positions, not independently verified exact numeric values from the app UI.

### 5.4 UUID layout hypothesis

Observed example:

`71000247-0400-265d-0302-6400000000aa`

Candidate interpretation:

- `71000247`: family/prefix plus a changing byte;
- `0400-265d`: stable marker;
- `0302`: suction channel/mode;
- first byte of `6400000000aa`: value `0x64` (100);
- last byte may be checksum/sequence/derived byte;
- other changing bytes have not been decoded.

This is a working hypothesis only.

## 6. Key unresolved identity question

The strongest current theory is that the packets may be emitted by the iPhone app rather than by the toy:

- manufacturer ID is Apple `0x004C`;
- the iOS app has previously been observed with both central and peripheral Bluetooth background modes;
- prior binary-symbol inspection found `CBPeripheralManager` and `startAdvertisingWithServiceUUID:`-style symbols;
- the packets change exactly when the app sliders or gravity mode change.

If this is correct, connecting to the random address with `BleakClient` is the wrong goal. The address would identify a temporary iPhone advertisement, while the toy may receive commands by scanning those advertisements.

This must be tested, not assumed.

## 7. Prior iOS/macOS app observations (raw extraction not included in this session)

Previously observed app location and binary facts:

- app bundle: `/Applications/Cachito.app/Wrapper/CachitoiOS.app`;
- executable: `CachitoiOS`;
- architecture: arm64;
- Info.plist indicated Bluetooth connection permissions and background modes `bluetooth-central` and `bluetooth-peripheral`;
- noteworthy symbols/strings included:
  - `BleManager`
  - `AdvertisHelper`
  - `ToyCommondModel`
  - `UserRemoteCommandModel`
  - `CustomModePlayManager`
  - `BTModeData`
  - `OOMWritenHandler`
  - `CBPeripheralManager`
  - `startAdvertisingWithServiceUUID:`
  - `ZJQserviceUUID:`
  - `writeValue:forCharacteristic:type:`
  - `dataOutCharacteristic`

These clues suggest the app may support both advertisement-based control and connection/GATT writes. Claude should re-verify them against the actual binary before treating them as canonical.

## 8. Official remote-control path confirmed

The official app has:

- “发起远程” on the device-owning phone;
- “远程控制” on the controller phone;
- a temporary six-character invitation code;
- a successful end-to-end test where the second phone controlled the first phone/device path.

The actual code used in testing is intentionally omitted because it is an ephemeral credential.

Likely architecture:

`toy <-BLE-> host app <-cloud/WebSocket or similar-> remote app`

The user-facing code may be only a lookup key; server URL, session token, and transport details can remain internal to the app.

A reference screenshot from an unrelated/analogous implementation describes a session + WebSocket route. It is evidence for a possible architecture, not evidence of Cachito’s exact API or message format.

## 9. Candidate implementation routes

### Route A - reverse the official remote session (preferred if accessible)

Goal: emulate the remote-controller app, while the official host app remains the BLE gateway.

Evidence supporting it:

- official six-character remote session works;
- avoids random BLE-address handling;
- host app already solves pairing, reconnect, and toy-specific transport.

Required observations:

1. network requests made when a host session is created;
2. request made when a controller submits the six-character code;
3. returned session/token/server details;
4. WebSocket/SSE/HTTP transport;
5. messages sent by suction, piston, pause, and gravity controls;
6. authentication, expiry, heartbeat, and reconnect rules.

Methods, in escalating order:

- ordinary HTTPS proxy capture using a test device and installed CA;
- inspect app strings/config for host names and endpoints;
- runtime instrumentation if TLS pinning or encrypted payloads block proxying;
- static analysis around `UserRemoteCommandModel` and remote-control classes.

Do not publish live invitation codes, tokens, or account credentials.

### Route B - reproduce app BLE advertisements

Goal: have another BLE peripheral broadcaster emit the same `710002..` service UUID sequence as the iPhone app.

Evidence supporting it:

- command-correlated data appears inside advertised Service UUIDs;
- iOS peripheral-mode clues exist;
- random address belongs naturally to an advertiser.

Risks:

- Windows + Bleak is mainly a central/scanner/client stack and does not provide a portable BLE peripheral advertiser API;
- may require macOS CoreBluetooth, Linux BlueZ, ESP32, or nRF52;
- timing, rotation, checksum, sequence byte, and device association may matter;
- merely replaying one UUID may be insufficient.

Needed tests:

- stop/kill the Cachito app and observe whether the `710002` advertiser disappears;
- disconnect or power off the toy and observe whether it persists;
- replay one known harmless pause/zero advertisement using peripheral-capable hardware;
- test whether the toy responds without the official app.

### Route C - direct GATT connection to the toy

Goal: discover the actual toy, connect, list GATT services, and reproduce writes.

Evidence supporting it:

- binary symbols include `writeValue:forCharacteristic:type:` and `dataOutCharacteristic`;
- the app requests central-mode Bluetooth.

Needed tests:

- scan with the official app disconnected to reveal the toy’s own advertisement;
- use the scanned `BLEDevice` object, not a permanently stored address;
- connect read-only and enumerate GATT services/characteristics;
- instrument the app to capture exact writes and characteristic UUIDs;
- test zero/pause only before any nonzero write.

Do not assume the `710002` advertiser is connectable.

### Route D - UI automation of the official app

Goal: automate the official controller UI rather than reverse a protocol.

Advantages:

- lowest protocol risk;
- app retains responsibility for safety and reconnection.

Disadvantages:

- fragile layout/accessibility dependency;
- difficult headless operation;
- poor latency and limited AI integration;
- not ideal as a final architecture.

Use only as a fallback or temporary prototype.

## 10. Recommended decision tree

1. First establish who emits `710002`:
   - app killed, toy on;
   - app open, toy off;
   - app open, toy on;
   - compare presence, RSSI, and address behavior.
2. In parallel, capture one official remote session network flow.
3. If remote flow is readable and stable, choose Route A.
4. If remote flow is pinned/opaque but `710002` is app advertising, choose Route B and use peripheral-capable hardware.
5. If a separate connectable toy advertisement and writable GATT service are found, choose Route C.
6. Keep Route D only as fallback.

## 11. What not to do yet

- Do not hard-code either observed MAC address.
- Do not equate “seen in scan” with “connectable”.
- Do not fit and ship an intensity formula from six approximate slider points.
- Do not send unverified nonzero writes.
- Do not build voice/countdown/AI control before transport is proven.
- Do not rewrite the working scanner while investigating the protocol.

## 12. Safety and test discipline

- Prefer unloaded/bench testing.
- Keep immediate physical power-off available.
- Begin with read-only enumeration and pause/zero commands.
- Rate-limit experimental writes.
- Log timestamp, transport, address/session, command, and response.
- Treat remote codes and tokens as secrets.

## 13. Included files

- current scanner and ASCII launchers;
- v2, v5, original v6, debugged v6, and slider-capture-fixed archives;
- two guided scan logs with local username redacted;
- static normalized sample CSV;
- parser script;
- reference screenshot;
- missing-original-document manifest.
