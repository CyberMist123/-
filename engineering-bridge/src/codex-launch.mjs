import fs from "node:fs";
import path from "node:path";

export function resolveCodexLaunch(env = process.env, platform = process.platform) {
  if (platform !== "win32") {
    return { command: "codex", env };
  }

  const home = String(env.USERPROFILE || env.HOME || "").trim();
  const localAppData = String(env.LOCALAPPDATA || "").trim();
  const candidates = [];

  if (home) {
    candidates.push(path.join(home, ".codex", "packages", "standalone", "current", "bin", "codex.exe"));
  }
  if (localAppData) {
    candidates.push(path.join(localAppData, "Programs", "OpenAI", "Codex", "bin", "codex.exe"));
  }

  const command = candidates.find((candidate) => fs.existsSync(candidate)) || "codex.exe";
  const childEnv = { ...env };

  if (home) {
    const standaloneRoot = path.join(home, ".codex", "packages", "standalone", "current");
    const resources = path.join(standaloneRoot, "codex-resources");
    const bin = path.join(standaloneRoot, "bin");
    const prepend = [resources, bin].filter((candidate) => fs.existsSync(candidate));
    if (prepend.length > 0) {
      childEnv.PATH = [...prepend, String(env.PATH || "")].filter(Boolean).join(path.delimiter);
    }
  }

  return { command, env: childEnv };
}
