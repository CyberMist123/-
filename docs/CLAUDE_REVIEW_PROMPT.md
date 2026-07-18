# Claude review prompt

Review this repository read-only first. Do not rewrite the scanner or create a new version before reporting findings.

Read:

1. `docs/CACHITO_RESEARCH_HANDOFF.md`
2. `analysis/static_samples.csv`
3. the clean redacted scan log inside the bundle
4. the current Windows scanner source inside the bundle

Please answer:

1. Can the `710002..` advertiser be identified as the phone app or the connected BLE accessory from current evidence?
2. What minimum read-only experiment distinguishes them?
3. Is Windows with Bleak suitable for the final transport, or would BLE peripheral advertising need another platform or small development board?
4. What read-only GATT enumeration test should run next?
5. For the confirmed official six-character remote session, what observations are needed to document its public client/server flow without exposing credentials?
6. Separate confirmed UUID fields, strong correlations, and speculation.
7. Rank the four routes in the handoff by effort, reliability, and dependency risk.
8. Propose one bounded next test with clear success and failure criteria.

Constraints:

- No v7.
- No project-wide refactor.
- No unverified nonzero BLE write.
- Preserve the Windows encoding rules.
- Report uncertainty explicitly.
- Give diagnosis and a test plan before code.
