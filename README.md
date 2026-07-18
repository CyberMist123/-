# Cachito control research handoff

This repository is a technical handoff for reviewing Cachito control paths. It contains the Windows BLE scanner snapshots, two guided scan datasets, normalized observations, prior iOS-app observations, competing implementation routes, and a review prompt for Claude.

Start here:

1. `docs/CACHITO_RESEARCH_HANDOFF.md` - current facts, uncertainties, and full decision tree.
2. `docs/CLAUDE_REVIEW_PROMPT.md` - bounded review request; asks for diagnosis before code.
3. `analysis/static_samples.csv` - compact samples from the clean 21-step run.
4. `bundle/cachito-research-handoff-20260719.zip` - full bundle: logs, all scanner archives, current extracted source, parser, screenshot, and manifest.

Important: this is a research snapshot, not a finished controller. No BLE write command has been verified yet. Do not infer that a changing advertisement address is automatically a connectable toy address.

The previously shared `Mac&APP逃课攻略.docx`, `toy.docx`, and `Tidal-Memory-AI接入代码手册.pdf` could not be retrieved from the current runtime. They are explicitly listed as missing rather than reconstructed or silently omitted.
