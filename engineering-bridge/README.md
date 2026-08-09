# Engineering Bridge v0.2.0-alpha.4

Minimal bridge: `ChatGPT -> GitHub issue -> local Engineering Bridge -> Codex CLI -> GitHub issue comment`.

Current Windows alpha.4 problem to fix: on the user's machine, double-clicking `start.cmd` opens an elevated `cmd.exe` window that stays visually blank. The prior alpha.3 successfully polled GitHub and invoked Codex, but Codex's local command executor failed because `codex-windows-sandbox-setup.exe` was not found. Alpha.4 changed the launcher to prefer `~/.codex/packages/standalone/current/bin/codex.exe`, prepend `codex-resources`, and use `shell:false`; after that, the start window shows no visible startup/status output and we do not yet have a proven end-to-end success.

Keep the implementation minimal. Do not add a web UI, database, worker pool, retries, daemon/service framework, new channel abstraction, or CyberBoss integration. Preserve the project allowlist and GitHub issue queue design.

Local Windows file conventions: `.ps1` UTF-8 BOM; `.cmd` ASCII-preferred UTF-8 no BOM; `.cmd` is launcher only.
