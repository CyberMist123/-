# Cachito BLE scan findings

This file preserves the meaningful information from the two uploaded scan logs in a reviewable Markdown form. Local Windows paths/usernames are omitted.

## Runs

| run | scanner flow | candidate advertiser | result |
|---|---|---|---|
| `20260719-053312` | original guided sequence; action labels started before slider adjustment finished | `55:32:AC:CE:F6:8B` | useful for discovering packet family and gravity behavior; static values can be time-shifted |
| `20260719-055407` | corrected PREPARE/CAPTURE sequence | `7D:C2:DC:2A:3E:B6` | clean 21-step run; preferred source for labeled samples |

The candidate address changed between runs but remained stable inside each run.

## Repeated target fingerprint

Packets correlated with Cachito actions repeatedly showed:

```text
Address: run-specific private/random-looking address
Manufacturer company: 0x004C
Manufacturer payload: 0100000000000000000000020000000000
Service UUID family: 710002??-0400-265d-????-????????????
```

Correlated mode fields:

```text
0302 → suction-related packets
050a → piston-related packets
0601 → appeared when gravity mode was enabled in the first run
```

The Apple company ID and app static evidence make a phone-originated advertisement plausible, but not proven.

## Clean static captures

Each static capture lasted six seconds and began only after the user set the requested slider target.

| step | user-labeled state | mode | observed first value byte | decimal |
|---:|---|---|---:|---:|
| 1 | baseline: suction 0, piston 0, gravity off | `0302` | `00` | 0 |
| 2 | suction 1 | `0302` | `00` | 0 |
| 3 | suction 10 | `0302` | `20` | 32 |
| 4 | suction 25 | `0302` | `2B` | 43 |
| 5 | suction 50 | `0302` | `3E` | 62 |
| 6 | suction 75 | `0302` | `51` | 81 |
| 7 | suction 100 | `0302` | `64` | 100 |
| 8 | suction returned to 0 | `0302` | `00` | 0 |
| 9 | piston 1 | `050a` | `01` | 1 |
| 10 | piston 10 | `050a` | `20` | 32 |
| 11 | piston 25 | `050a` | `2B` | 43 |
| 12 | piston 50 | `050a` | `3E` | 62 |
| 13 | piston 75 | `050a` | `51` | 81 |
| 14 | piston 100 | `050a` | `64` | 100 |
| 15 | piston returned to 0 | `050a` | `01` | 1 |

Important uncertainty:

- suction target 1 produced `00`;
- piston baseline/return-to-zero behavior appears to use `01`;
- the labels refer to slider positions selected in the UI, not independently read exact numeric values;
- do not derive or ship a formula from this table yet.

## Gravity mode captures

When gravity mode was active, packets became frequent and alternated between `0302` and `050a`.

### Step 16 — phone flat, screen up

```text
0302 value: 00
050a value: 01
```

Observed packets alternated repeatedly between the two channels.

### Step 17 — phone vertical, screen facing user

```text
0302 value: mostly 3D (61)
050a value: mostly 3D (61), one 3C (60)
```

### Step 18 — phone tilted left about 45 degrees

```text
0302 value: 3A (58)
050a value: 3A (58)
```

### Step 19 — phone tilted right about 45 degrees

```text
0302 values: 37–38 (55–56)
050a values: 37–38 (55–56)
```

### Step 20 — dynamic flat → vertical → flat

The twelve-second capture showed a continuous transition rather than one fixed value.

Observed suction values included:

```text
00, 1A, 1B, 1F, 2B, 32, 39, 3B, 3C, 3D
```

Observed piston values included:

```text
01, 2B, 34, 37, 38, 39, 3A, 3B, 3C
```

Representative adjacent sequence:

```text
0302:00
050a:01
0302:2B
0302:32
050a:2B
050a:37
050a:3B
050a:3A
050a:39
0302:3C
050a:34
050a:3C
050a:3B
0302:3B
0302:3D
0302:3B
0302:39
050a:38
050a:34
0302:1F
0302:1B
0302:1A
```

This supports the interpretation that gravity mode continuously maps phone pose/motion into values for both channels.

### Step 21 — gravity off, both controls returned to pause/zero

```text
0302 value: 00
050a value: 01
```

## UUID structure observations

Example:

```text
71000247-0400-265d-0302-6400000000aa
```

Strong correlations:

- `0400-265d` is stable in the target family;
- `0302` / `050a` select or identify the channel;
- the first byte of the final group tracks the observed output value;
- the first group's final byte and final byte of the UUID vary across otherwise equivalent states.

Unresolved fields may represent a counter, whitening/checksum output, randomization, device association, or another derived value. A single captured UUID must not be replayed as though those bytes are irrelevant.

## Data-quality notes

- The first run remains useful for chronology and the appearance of `0601`, but its static action labels can include slider transit values.
- The second run is the canonical labeled dataset.
- The scanner deduplicates identical advertiser fingerprints per address and clears the cache at each `CAPTURE START`; packet counts are therefore not raw radio transmission counts.
- Nearby unrelated Apple/Chromecast advertisements are present in both logs and must be filtered by the complete target fingerprint, not RSSI alone.

## Reproducibility

The current scanner source is under `tools/windows-scanner/`.

The read-only parser is under `analysis/parse_cachito_log.py` and extracts only service UUIDs matching:

```regex
710002[0-9a-f]{2}-0400-265d-(0302|050a|0601)-([0-9a-f]{12})
```
