// Small JSON file helpers: reads that tolerate a missing file, and writes that replace the file in one step.
import { mkdir, readFile, rename, writeFile } from "node:fs/promises";
import { homedir } from "node:os";
import { dirname, join } from "node:path";

export async function readJson(path, fallback) {
    try {
        return JSON.parse(await readFile(path, "utf8"));
    } catch (error) {
        if (error.code === "ENOENT") return fallback;
        throw error;
    }
}

const queues = new Map();

// Writes to one path run one after another, so concurrent updates never interleave.
export function writeJson(path, value) {
    const previous = queues.get(path) || Promise.resolve();
    const next = previous.catch(() => {}).then(async () => {
        await mkdir(dirname(path), { recursive: true });
        const temporary = `${path}.${process.pid}.tmp`;
        await writeFile(temporary, JSON.stringify(value, null, 1) + "\n", "utf8");
        await rename(temporary, path);
    });
    queues.set(path, next);
    return next;
}

// Where a canvas keeps what belongs to this conversation: the session's files, else the user's extension artifacts.
export function sessionFiles(session, name) {
    if (session?.workspacePath) return join(session.workspacePath, "files", name);
    const home = process.env.COPILOT_HOME || join(homedir(), ".copilot");
    return join(home, "extensions", "orchi-canvases", "artifacts", name);
}
