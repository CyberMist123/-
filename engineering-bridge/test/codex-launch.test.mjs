import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { resolveCodexLaunch } from "../src/codex-launch.mjs";

test("Windows prefers standalone Codex binary and resources", () => {
  const home = fs.mkdtempSync(path.join(os.tmpdir(), "bridge-codex-"));
  const root = path.join(home, ".codex", "packages", "standalone", "current");
  const bin = path.join(root, "bin");
  const resources = path.join(root, "codex-resources");
  fs.mkdirSync(bin, { recursive: true });
  fs.mkdirSync(resources, { recursive: true });
  fs.writeFileSync(path.join(bin, "codex.exe"), "");

  const result = resolveCodexLaunch({ USERPROFILE: home, PATH: "BASE" }, "win32");
  assert.equal(result.command, path.join(bin, "codex.exe"));
  assert.ok(result.env.PATH.startsWith(`${resources}${path.delimiter}${bin}${path.delimiter}`));
});

test("Windows falls back to codex.exe when no known install exists", () => {
  const result = resolveCodexLaunch({ USERPROFILE: "", LOCALAPPDATA: "", PATH: "BASE" }, "win32");
  assert.equal(result.command, "codex.exe");
  assert.equal(result.env.PATH, "BASE");
});
