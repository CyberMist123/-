const START = "<!-- engineering-bridge-task";
const END = "-->";

export function parseTask(body) {
  const text = String(body || "");
  const start = text.indexOf(START);
  if (start < 0) throw new Error("missing engineering-bridge-task block");
  const end = text.indexOf(END, start + START.length);
  if (end < 0) throw new Error("unterminated engineering-bridge-task block");

  let raw = text.slice(start + START.length, end).trim();
  if (raw.startsWith("```json")) raw = raw.slice(7).trim();
  if (raw.startsWith("```")) raw = raw.slice(3).trim();
  if (raw.endsWith("```")) raw = raw.slice(0, -3).trim();

  let task;
  try {
    task = JSON.parse(raw);
  } catch (error) {
    throw new Error(`invalid task JSON: ${error.message}`);
  }

  const project = String(task.project || "").trim();
  const prompt = String(task.prompt || "").trim();
  if (!project) throw new Error("task.project is required");
  if (!prompt) throw new Error("task.prompt is required");
  return { project, prompt };
}

export function taskBlock({ project, prompt }) {
  return `${START}\n${JSON.stringify({ project, prompt }, null, 2)}\n${END}`;
}
