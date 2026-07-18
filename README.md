# Cachito control research handoff

This Draft PR is the GitHub-only handoff for reviewing Cachito control paths. It now contains the verified Windows scanner source, normalized scan findings, recovered app static evidence, prior reference documents transcribed to Markdown, the official remote-session hypothesis, and a bounded review prompt for Claude.

## Read first

1. `docs/CACHITO_RESEARCH_HANDOFF.md` — current facts, uncertainties, and route decision tree.
2. `docs/CLAUDE_REVIEW_PROMPT.md` — the exact read-only review task.
3. `data/SCAN_FINDINGS.md` — both scan runs, static samples, and gravity-mode sequences.
4. `evidence/CACHITO_APP_STATIC_EVIDENCE.md` — recovered Info.plist and Objective-C metadata facts.
5. `references/CHEMTRAILS_REVIEW.md` — assessment of `Kristenkristen/Chemtrails` and why its ten-element `vib` protocol must not be assumed for Cachito.
6. `tools/windows-scanner/` — current v6 scanner, ASCII launchers, and usage notes.
7. `documents/originals_as_markdown/` — recovered Word/PDF references converted to Markdown.

## Important state

This is a research snapshot, not a finished controller.

- No BLE write command has been verified.
- No remote API message for Cachito has been verified.
- A changing advertisement address is not automatically a connectable accessory address.
- The six-character official remote-control code works app-to-app, but its server/session protocol is still unknown.
- No v7 or project rewrite is included.

The original binary Word/PDF files are not committed; their recovered text is preserved as Markdown so Claude can review everything from GitHub without a separate local bundle.
