# Cachito control research handoff

This branch is a technical handoff for reviewing Cachito control paths. It contains the verified Windows debugging facts, normalized BLE samples, prior iOS-app observations, competing implementation routes, and a bounded review prompt for Claude.

Start here:

1. `docs/CACHITO_RESEARCH_HANDOFF.md` - current facts, uncertainties, and decision tree.
2. `docs/CLAUDE_REVIEW_PROMPT.md` - asks for diagnosis and one bounded next test before code.
3. `analysis/static_samples.csv` - compact samples from the clean 21-step run.
4. `documents/REUPLOAD_REQUIRED.md` - originals that could not be retrieved from this runtime.

Important: this is a research snapshot, not a finished controller. No BLE write command has been verified. Do not infer that a changing advertisement address is automatically a connectable accessory address.

The previously shared `Mac&APP逃课攻略.docx`, `toy.docx`, and `Tidal-Memory-AI接入代码手册.pdf` were not accessible from the current runtime. They are explicitly listed as missing rather than reconstructed or silently omitted.
