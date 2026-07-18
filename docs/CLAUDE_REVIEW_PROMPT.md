# Claude review prompt

Review this repository read-only first. Do not rewrite the scanner, create a new version, or send a control command before reporting findings.

## Read in this order

1. `docs/CACHITO_RESEARCH_HANDOFF.md`
2. `data/SCAN_FINDINGS.md`
3. `evidence/CACHITO_APP_STATIC_EVIDENCE.md`
4. `references/CHEMTRAILS_REVIEW.md`
5. `analysis/static_samples.csv`
6. `tools/windows-scanner/cachito_scan_gui_v6.py`
7. `documents/originals_as_markdown/toy.md`
8. `documents/originals_as_markdown/Mac_APP_escape_guide.md`
9. `documents/originals_as_markdown/Signal_Bridge_Guide_for_Claude.md`

`Tidal-Memory-AI接入代码手册.md` is preserved because the user requested the prior reference set; it is not protocol evidence.

## Questions

1. From the BLE packet structure, Apple company ID, app background modes, and Objective-C metadata, can `710002..` be identified as phone-originated or accessory-originated? Separate proof from probability.
2. What minimum read-only experiment distinguishes the advertiser identity?
3. Does the static metadata suggest advertisement-only control, GATT-only control, or a hybrid? Which exact methods/classes should be inspected next?
4. Is Windows/Bleak suitable for the final transport? Distinguish scanning/GATT-client support from BLE peripheral advertising.
5. What read-only GATT enumeration test should run if a separate accessory advertisement is found?
6. Interpret the changing UUID fields. Separate confirmed fields, strong correlations, and speculation. Do not infer a production intensity formula from approximate slider positions.
7. Review `Kristenkristen/Chemtrails`: confirm whether the forum screenshot's ten-element `vib` description is MonsterParty-specific, and identify only the architecture/testing ideas reusable for Cachito.
8. For Cachito's confirmed six-character app-to-app remote session, list the minimum observations required to determine REST/WebSocket/SSE/polling behavior without exposing credentials.
9. Rank these routes by expected effort, reliability, hardware dependency, cloud dependency, and maintenance risk:
   - official remote-session emulation;
   - app BLE advertisement reproduction;
   - direct accessory GATT;
   - official UI automation;
   - Intiface/Signal Bridge if supported.
10. Propose exactly one bounded next test with clear success/failure criteria and no feature expansion.

## Constraints

- No v7.
- No project-wide refactor.
- No unverified nonzero BLE write.
- No copying MonsterParty endpoints/op codes/array format into Cachito.
- Preserve the Windows encoding rules.
- Report uncertainty explicitly.
- Give diagnosis and a test plan before code.
- Treat invitation codes, tokens, sessions, and account data as secrets.
