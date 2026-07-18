# Cachito research handoff — 2026-07-19

## 1. Goal and boundaries

Goal: identify the shortest reliable way to control a Cachito accessory from an AI-accessible program.

Desired later behavior, not yet implemented:

- suction channel: pause/0 plus apparent 1-100 UI slider;
- piston channel: pause/0 plus apparent 1-100 UI slider;
- “嗨翻” means gravity/tilt control;
- voice, countdown, and action logs are later layers.

Current phase is transport/protocol identification only.

Hard constraints:

- no v7;
- no project-wide rewrite;
- no guessed protocol fields;
- no unverified nonzero BLE write;
- diagnosis and bounded tests before feature work.

## 2. Windows environment and startup diagnosis

Verified manually:

- Python `C:\Python314\python.exe`, version 3.14.4, 64-bit;
- pip 26.1.1;
- tkinter 8.6;
- bleak imports correctly;
- minimal Tkinter GUI works;
- minimal `BleakScanner.discover(timeout=8.0)` works;
- minimal Tkinter plus background BLE scan works.

The original v6 startup failure was caused by the launcher layer, not Python/Tkinter/Bleak. The old `.cmd` files used UTF-8 BOM and Chinese command text, which could become garbled under `cmd.exe` before Python started.

Encoding rules fixed for future work:

- `.ps1`: UTF-8 with BOM for Windows PowerShell 5.1 compatibility;
- `.py`, `.json`, `.md`: UTF-8 without BOM;
- `.bat`/`.cmd`: English ASCII only, UTF-8 without BOM, launcher logic only;
- do not change system locale, registry, or global code page to hide encoding faults.

The working scanner and launchers are committed under `tools/windows-scanner/`.

## 3. Scanner data-quality fix

The first guided scanner mislabeled intermediate values because capture began as soon as a target was displayed. The official control is a continuous slider, so moving between targets produces intermediate broadcasts.

The corrected v6 state machine is:

1. PREPARE: user adjusts slider or phone pose; no capture label is written.
2. User clicks `已调好，开始采样`.
3. CAPTURE: clear dedup cache, write `CAPTURE START`, collect for 6 seconds (12 seconds for dynamic movement), then write `CAPTURE END`.
4. Advance to the next PREPARE step.

The clean run completed all 21 captures.

## 4. BLE observations

Two runs showed a strong advertiser carrying packets correlated with Cachito actions:

- first run: `55:32:AC:CE:F6:8B`;
- clean run: `7D:C2:DC:2A:3E:B6`.

The address changed between runs but stayed stable during each run. This is consistent with a private/random BLE address, but does not identify whether the advertiser is the phone or accessory.

Repeated target structure:

- Service UUID prefix `710002..`;
- stable middle `0400-265d`;
- `0302` correlates with suction;
- `050a` correlates with piston;
- an earlier run showed `0601` when gravity mode was enabled;
- Apple manufacturer company ID `0x004C` repeatedly appeared with payload `0100000000000000000000020000000000`.

Example at the user-labeled 100 suction position:

```text
71000247-0400-265d-0302-6400000000aa
```

Working interpretation only:

- `0302` is a suction-related channel/mode field;
- the first byte of the final group tracks the observed output value (`64` hex = 100);
- the first group’s final byte and the UUID’s final byte vary and may be sequence/checksum/derived fields.

Full derived findings, including gravity-mode sequences, are in `data/SCAN_FINDINGS.md`.

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

The middle points look regular, but no formula should be shipped from these approximate positions. Exact UI numeric values were not independently verified.

Gravity mode provided stronger behavioral evidence:

- flat: suction `00`, piston `01`;
- vertical: mostly `3D` on both channels;
- left ~45°: `3A` on both;
- right ~45°: `37`–`38` on both;
- dynamic movement produced continuous transitions across both channels.

## 6. Critical advertiser identity question

The strongest current hypothesis is that `710002..` may be emitted by the iPhone app rather than by the accessory:

- manufacturer company ID is Apple `0x004C`;
- app metadata declares both `bluetooth-central` and `bluetooth-peripheral` background modes;
- recovered metadata includes `CBPeripheralManager`, `AdvertisHelper`, and `startAdvertisingWithServiceUUID:`-style symbols;
- packets change exactly when app sliders or gravity mode change.

If true, connecting to the random address with `BleakClient` is the wrong goal. It may be a temporary phone advertisement while the accessory scans those advertisements.

This remains unverified. `evidence/CACHITO_APP_STATIC_EVIDENCE.md` records the supporting facts and limits.

## 7. Recovered app static evidence

Recovered facts include:

- bundle identifier `com.Cachito.CachitoiOS`;
- app version 1.7.8;
- `NSAllowsArbitraryLoads = true`;
- background modes `bluetooth-central`, `bluetooth-peripheral`, `fetch`, and `processing`;
- classes/properties such as `BleManager`, `AdvertisHelper`, `ToyCommondModel`, `UserRemoteCommandModel`, `CustomModePlayManager`, `BTModeData`, `serviceUUID`, `deviceId`, `remoteId`, and `codeString`;
- Bluetooth-related strings including `writeValue:forCharacteristic:type:` and `dataOutCharacteristic`.

This suggests both advertisement and GATT paths may exist. It does not yet show which path controls this specific accessory or how changing UUID bytes are constructed.

## 8. Official remote path confirmed

The official app provides:

- `发起远程` on the host phone;
- `远程控制` on a second phone;
- a temporary six-character invitation code;
- a successful end-to-end control test.

The actual test code is intentionally omitted as an ephemeral credential.

Likely architecture:

```text
accessory <-BLE-> host app <-cloud session-> remote app
```

The six-character code may be only a lookup key; server URL, session token, heartbeat, and transport can remain internal to the app.

## 9. Chemtrails reference and the forum screenshot

`Kristenkristen/Chemtrails` implements an AI-oriented WebSocket controller for the MonsterParty backend.

Its documented flow is:

1. browser-openable remote URL contains a token;
2. REST endpoint resolves it into WebSocket/session/user fields;
3. controller joins the WebSocket session;
4. server returns a handle and device-ready state;
5. control uses a ten-element 0-100 `vib` array;
6. an application heartbeat keeps the session alive.

The forum screenshot’s description of a share link, REST lookup, WebSocket, and ten-element `vib` array matches Chemtrails extremely closely. It is therefore likely MonsterParty-specific or derived from that implementation, not a generic rule for all toys.

Direct Cachito compatibility is not established because Cachito exposes only an app-entered six-character code, not a browser-openable token URL.

Reusable lesson:

- a hidden Cachito REST + WebSocket session remains plausible;
- observe Cachito’s own code exchange and frames;
- do not copy MonsterParty endpoints, op codes, heartbeat, array length, or motor mapping.

See `references/CHEMTRAILS_REVIEW.md`.

## 10. Candidate routes

### A. Document and emulate the official remote-controller flow

Preferred if Cachito’s client/server flow is observable and stable. The host app continues handling BLE pairing and random addresses.

Needed evidence:

- host session creation request;
- controller code-submission request;
- returned session/server/user/device fields;
- WebSocket/SSE/polling transport;
- join, ready, control, stop, heartbeat, expiry, and reconnect behavior.

Chemtrails increases confidence that this architecture can be practical, but does not supply Cachito’s protocol.

### B. Reproduce the app’s BLE advertisements

Plausible if the phone is the `710002..` advertiser. Windows/Bleak is mainly a central/client stack and may not be suitable for peripheral advertising. macOS CoreBluetooth, Linux BlueZ, ESP32, or nRF52 may be required.

Unknowns:

- changing UUID/checksum bytes;
- timing and rotation;
- device association;
- whether a native encoding routine is involved.

The `toy.docx` precedent warns that proprietary broadcast protocols can require whitening, CRC, bit reversal, and address prefixes. Its exact Android/manufacturer details are unrelated to Cachito, but the warning against guessing is directly relevant.

### C. Connect directly to the accessory over GATT

Plausible because app symbols mention characteristic writes. First reveal the accessory’s own advertisement while the official app is disconnected, then perform read-only service/characteristic enumeration using the scanned `BLEDevice` object.

Do not assume the `710002..` advertiser is connectable.

### D. Automate the official UI

Lowest protocol risk but fragile, difficult to run headlessly, and poor as a long-term AI integration. Keep only as fallback.

### E. Intiface / Signal Bridge path

The previously shared Signal Bridge guide is preserved as Markdown. This route becomes attractive only if Intiface already supports the accessory or a stable local controller exists.

It is downstream infrastructure, not evidence for Cachito’s transport.

## 11. Recommended next decision test

First establish who emits `710002..` without writing anything:

1. app force-quit, accessory on;
2. app open, accessory off/disconnected;
3. app open, accessory on;
4. compare presence, RSSI, address, and packet behavior.

In parallel, document one official remote session’s ordinary client/server flow without publishing codes or credentials.

Decision:

- readable/stable remote flow -> Route A;
- phone advertisement confirmed and remote flow opaque -> Route B;
- separate connectable accessory plus writable GATT service found -> Route C;
- verified Intiface support -> Route E;
- otherwise temporary Route D.

## 12. Safety and exclusions

- Do not hard-code either observed address.
- `Seen in scan` does not mean `connectable`.
- Do not ship a value formula from approximate slider positions.
- Begin with read-only enumeration and pause/zero tests.
- Prefer unloaded bench testing and keep physical power-off available.
- Rate-limit experiments and log timestamp, transport, session/address, command, and result.
- Do not publish invitation codes, tokens, or account credentials.
- A tunnel URL alone is not authentication.
- A final controller must provide ordinary stop, emergency all-stop, parameter bounds, and `try/finally` cleanup.

## 13. GitHub contents

Core:

- `README.md`
- `docs/CACHITO_RESEARCH_HANDOFF.md`
- `docs/CLAUDE_REVIEW_PROMPT.md`
- `data/SCAN_FINDINGS.md`
- `analysis/static_samples.csv`
- `analysis/parse_cachito_log.py`

Evidence:

- `evidence/CACHITO_APP_STATIC_EVIDENCE.md`
- `references/CHEMTRAILS_REVIEW.md`

Working diagnostic tool:

- `tools/windows-scanner/cachito_scan_gui_v6.py`
- `tools/windows-scanner/start_cachito.cmd`
- `tools/windows-scanner/diagnostic.cmd`
- `tools/windows-scanner/README.md`

Recovered prior references as Markdown:

- `documents/originals_as_markdown/toy.md`
- `documents/originals_as_markdown/Mac_APP_escape_guide.md`
- `documents/originals_as_markdown/Tidal-Memory-AI接入代码手册.md`
- `documents/originals_as_markdown/Signal_Bridge_Guide_for_Claude.md`

The original binary Word/PDF files and raw scan logs are not required for the Claude review because their relevant content and derived data are now represented in GitHub text files. The original binaries have not been misrepresented as committed originals.
