import fs from "node:fs";
import path from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import { parseTask } from "./task.mjs";
import { resolveCodexLaunch } from "./codex-launch.mjs";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.dirname(HERE);
const args = new Set(process.argv.slice(2));
const once = args.has("--once");
const configPath = process.env.ENGINEERING_BRIDGE_CONFIG || path.join(ROOT, "config.local.json");
const QUEUED = "[bridge:queued]";
const RUNNING = "[bridge:running]";
const DONE = "[bridge:done]";
const FAILED = "[bridge:failed]";

function loadConfig() {
  const config = JSON.parse(fs.readFileSync(configPath, "utf8"));
  if (!config.controlRepo || typeof config.projects !== "object") {
    throw new Error("config requires controlRepo and projects");
  }
  return config;
}

function run(command, argv, options = {}) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, argv, {
      cwd: options.cwd,
      shell: false,
      windowsHide: true,
      env: options.env || process.env,
      stdio: [options.input === undefined ? "ignore" : "pipe", "pipe", "pipe"],
    });
    let stdout = "";
    let stderr = "";
    child.stdout.setEncoding("utf8");
    child.stderr.setEncoding("utf8");
    child.stdout.on("data", (chunk) => { stdout += chunk; });
    child.stderr.on("data", (chunk) => { stderr += chunk; });
    child.on("error", reject);
    child.on("close", (code) => resolve({ code, stdout, stderr }));
    if (options.input !== undefined) {
      child.stdin.end(options.input, "utf8");
    }
  });
}

async function gh(repo, argv) {
  const result = await run("gh", [...argv, "--repo", repo]);
  if (result.code !== 0) throw new Error(result.stderr.trim() || `gh exited ${result.code}`);
  return result.stdout;
}

async function listQueued(repo) {
  const raw = await gh(repo, [
    "issue", "list",
    "--state", "open",
    "--search", `in:title "${QUEUED}"`,
    "--limit", "20",
    "--json", "number,title,body",
  ]);
  const issues = JSON.parse(raw || "[]").filter((issue) => String(issue.title || "").startsWith(QUEUED));
  return issues.sort((a, b) => a.number - b.number);
}

async function setState(repo, issue, fromPrefix, toPrefix) {
  const title = String(issue.title || "");
  if (!title.startsWith(fromPrefix)) throw new Error(`issue #${issue.number} is not in ${fromPrefix} state`);
  const nextTitle = `${toPrefix}${title.slice(fromPrefix.length)}`;
  await gh(repo, ["issue", "edit", String(issue.number), "--title", nextTitle]);
  issue.title = nextTitle;
}

async function comment(repo, number, body) {
  await gh(repo, ["issue", "comment", String(number), "--body", body]);
}

function projectRoot(config, project) {
  const root = config.projects[project];
  if (!root) throw new Error(`project is not allowlisted: ${project}`);
  const resolved = path.resolve(String(root));
  if (!fs.existsSync(resolved)) throw new Error(`project path does not exist: ${resolved}`);
  return resolved;
}

function finalMessageFromJsonl(stdout) {
  let last = "";
  for (const line of String(stdout || "").split(/\r?\n/)) {
    if (!line.trim()) continue;
    try {
      const event = JSON.parse(line);
      if (event.type === "item.completed" && event.item?.type === "agent_message") {
        last = String(event.item.text || "").trim() || last;
      }
    } catch {
      // codex --json should be JSONL; ignore incidental non-JSON output.
    }
  }
  return last;
}

function clip(text, max = 60000) {
  const value = String(text || "");
  return value.length <= max ? value : `${value.slice(0, max)}\n\n[truncated by Engineering Bridge]`;
}

async function executeIssue(config, issue) {
  const task = parseTask(issue.body);
  const cwd = projectRoot(config, task.project);

  await setState(config.controlRepo, issue, QUEUED, RUNNING);
  await comment(config.controlRepo, issue.number, `Engineering Bridge ${process.env.npm_package_version || "v0.2.0-alpha.4"}: started project \`${task.project}\`.`);

  const codex = resolveCodexLaunch();
  const result = await run(codex.command, [
    "-a", "never",
    "exec",
    "--json",
    "--sandbox", "workspace-write",
    "-C", cwd,
    "-",
  ], { cwd, input: task.prompt, env: codex.env });

  const finalMessage = finalMessageFromJsonl(result.stdout);
  const detail = finalMessage || result.stderr || result.stdout || "(no output)";
  const ok = result.code === 0;
  await comment(
    config.controlRepo,
    issue.number,
    clip(`Engineering Bridge: ${ok ? "completed" : "failed"} (exit ${result.code}).\n\n${detail}`),
  );
  await setState(config.controlRepo, issue, RUNNING, ok ? DONE : FAILED);
}

async function processOnce(config) {
  const issues = await listQueued(config.controlRepo);
  if (issues.length === 0) return false;
  const issue = issues[0];

  try {
    parseTask(issue.body);
  } catch (error) {
    await comment(config.controlRepo, issue.number, `Engineering Bridge: rejected task.\n\n${clip(error?.message || error)}`);
    await setState(config.controlRepo, issue, QUEUED, FAILED);
    return true;
  }

  try {
    await executeIssue(config, issue);
  } catch (error) {
    await comment(config.controlRepo, issue.number, `Engineering Bridge: failed before/during execution.\n\n${clip(error?.stack || error)}`);
    await setState(config.controlRepo, issue, RUNNING, FAILED);
    throw error;
  }
  return true;
}

async function main() {
  const config = loadConfig();
  do {
    const processed = await processOnce(config);
    if (once) break;
    if (!processed) {
      const waitMs = Math.max(1, Number(config.pollSeconds) || 10) * 1000;
      await new Promise((resolve) => setTimeout(resolve, waitMs));
    }
  } while (true);
}

main().catch((error) => {
  console.error(error?.stack || error);
  process.exitCode = 1;
});
