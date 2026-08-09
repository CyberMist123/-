import test from "node:test";
import assert from "node:assert/strict";
import { parseTask, taskBlock } from "../src/task.mjs";

test("round-trips a bridge task", () => {
  const body = `Do this task.\n\n${taskBlock({ project: "cyberboss", prompt: "Fix only the failing test." })}`;
  assert.deepEqual(parseTask(body), {
    project: "cyberboss",
    prompt: "Fix only the failing test.",
  });
});

test("rejects a missing task block", () => {
  assert.throws(() => parseTask("hello"), /missing engineering-bridge-task block/);
});

test("rejects missing project", () => {
  assert.throws(() => parseTask('<!-- engineering-bridge-task\n{"prompt":"x"}\n-->'), /task.project is required/);
});
