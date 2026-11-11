// The Orchi board: the pool's crews and backlog for one repository. It reads GitHub through the bundled board.py and
// what Orchi last reported through `update_pool`; it changes nothing in GitHub. A button the user confirms becomes a
// request in this conversation.
import { execFile } from "node:child_process";
import { readFile } from "node:fs/promises";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { CanvasError, createCanvas } from "@github/copilot-sdk/extension";
import { boardRequest } from "./requests.mjs";
import { startServer } from "./server.mjs";
import { readJson, sessionFiles, writeJson } from "./store.mjs";

const SCRIPT = fileURLToPath(new URL("../../../skills/orchi-core/scripts/board.py", import.meta.url));
const PAGE = fileURLToPath(new URL("../ui/board.html", import.meta.url));
const REPO = /^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/;
const EVERY = 5 * 60 * 1000;
const STATES = ["working", "waiting", "idle", "stuck", "free"];

const POOL_SCHEMA = {
    type: "object",
    additionalProperties: false,
    properties: {
        crews: {
            type: "array",
            description: "Every crew of the pool, as get_sessions_status shows it now.",
            items: {
                type: "object",
                required: ["name", "state"],
                additionalProperties: false,
                properties: {
                    name: { type: "string", description: "The crew's session name, `[<role>] <topic>`." },
                    session_id: { type: "string" },
                    state: { type: "string", enum: STATES, description: "waiting = needs the user's input." },
                    issue: { type: "integer", description: "The Issue it holds, when its claim does not show it." },
                    doing: { type: "string", description: "What it does now, in a few plain words." },
                    question: { type: "string", description: "Its question, while it waits for input." },
                    background: { type: "string", description: "Its background run, while it is idle." },
                    since: { type: "string", description: "ISO time of its last activity." },
                    stuck: { type: "string", description: "Why it is stuck, when Orchi knows." },
                },
            },
        },
        mode: { type: "string", enum: ["on", "off"], description: "Autonomous mode." },
        limit: { type: "integer", minimum: 1, description: "How many crews may hold work at once." },
        questions: {
            type: "array",
            description: "Orchi's own open questions to the user.",
            items: {
                type: "object",
                required: ["id", "text"],
                additionalProperties: false,
                properties: { id: { type: "string" }, text: { type: "string" } },
            },
        },
        merges: { type: "array", items: { type: "integer" }, description: "PRs waiting for the user's yes to merge." },
        deferred: { type: "array", items: { type: "integer" }, description: "Issues the user deferred." },
        held: { type: "array", items: { type: "integer" }, description: "PRs the user put on hold." },
    },
};

export function boardCanvas(host) {
    const instances = new Map(); // instanceId → { repo, server }
    const repos = new Map(); // repo → { snapshot, error, timer, running }

    const files = (repo) => {
        const base = join(sessionFiles(host.session, "orchi-board"), repo.replace("/", "__"));
        return { state: `${base}.state.json`, snapshot: `${base}.snapshot.json` };
    };

    async function entry(repo) {
        let item = repos.get(repo);
        if (!item) {
            item = { snapshot: await readJson(files(repo).snapshot, null).catch(() => null), error: null, running: null };
            repos.set(repo, item);
        }
        return item;
    }

    function push(repo, event) {
        for (const instance of instances.values()) if (instance.repo === repo) instance.server.push(event);
    }

    function python(args) {
        return new Promise((resolve, reject) => {
            const run = (command) =>
                execFile(command, args, { timeout: 120_000, maxBuffer: 32 * 1024 * 1024 }, (error, stdout, stderr) => {
                    if (error?.code === "ENOENT" && command === "python3") return run("python");
                    if (error && !stdout) return reject(new Error(String(stderr || error.message).trim()));
                    resolve(stdout);
                });
            run("python3");
        });
    }

    async function refresh(repo) {
        const item = await entry(repo);
        if (!item.running) {
            item.running = (async () => {
                try {
                    const document = JSON.parse(await python([SCRIPT, "--json", "--repo", repo, "--state", files(repo).state]));
                    if (document.error) throw new Error(document.error);
                    item.snapshot = document;
                    item.error = null;
                    await writeJson(files(repo).snapshot, document);
                } catch (error) {
                    item.error = String(error.message || error);
                    host.session?.log(`Orchi board: ${item.error}`, { level: "warning", ephemeral: true });
                } finally {
                    item.running = null;
                    push(repo, { type: "snapshot" });
                }
            })();
        }
        await item.running;
        return item;
    }

    function summary(item) {
        const crews = item.snapshot?.crews || [];
        const count = Object.fromEntries(["stuck", "waiting", "working", "background", "idle", "free"].map(
            (state) => [state, crews.filter((crew) => crew.state === state).length]));
        return { updated: item.snapshot?.updated || null, error: item.error, crews: count,
            waiting_for_user: (item.snapshot?.waiting || []).length, pulls: (item.snapshot?.pulls || []).length };
    }

    function repoOf(ctx) {
        const instance = instances.get(ctx.instanceId);
        if (!instance) throw new CanvasError("not_open", "Open the board first.");
        return instance.repo;
    }

    async function resolveRepo(input) {
        if (input?.repo) {
            if (!REPO.test(input.repo)) throw new CanvasError("bad_repo", "repo must be OWNER/NAME.");
            return input.repo;
        }
        return new Promise((resolve, reject) =>
            execFile("gh", ["repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner"], (error, stdout) =>
                error ? reject(new CanvasError("no_repo", "Pass repo (OWNER/NAME): this folder has no GitHub repository."))
                    : resolve(stdout.trim())));
    }

    async function route(repo, { method, path, body }) {
        if (method === "GET" && path === "/") return { type: "text/html; charset=utf-8", data: await readFile(PAGE, "utf8") };
        const item = await entry(repo);
        if (method === "GET" && path === "/state") {
            return { json: { repository: repo, snapshot: item.snapshot, error: item.error, refreshing: !!item.running } };
        }
        if (method === "POST" && path === "/refresh") {
            refresh(repo);
            return { json: { refreshing: true } };
        }
        if (method === "POST" && path === "/request") {
            const prompt = boardRequest(body);
            await host.session.send({ prompt });
            return { json: { sent: prompt } };
        }
        return null;
    }

    return createCanvas({
        id: "orchi-board",
        displayName: "Orchi board",
        description:
            "The Orchi pool of one repository: crews by what needs a look, the Initiative-Epic-Task backlog with PRs " +
            "and checks, and what waits for the user. Orchi keeps it current with update_pool.",
        inputSchema: {
            type: "object",
            additionalProperties: false,
            properties: { repo: { type: "string", description: "OWNER/NAME; defaults to this folder's repository." } },
        },
        actions: [
            {
                name: "refresh",
                description: "Read GitHub again and redraw the board. Returns the counts the user scans for.",
                inputSchema: { type: "object", properties: {}, additionalProperties: false },
                handler: async (ctx) => summary(await refresh(repoOf(ctx))),
            },
            {
                name: "update_pool",
                description:
                    "Report what only Orchi knows: the crews as get_sessions_status shows them, autonomous mode, the " +
                    "pool size, Orchi's open questions, PRs waiting for the user's merge, deferred Issues, held PRs. " +
                    "Fields you pass replace the stored ones; then the board refreshes.",
                inputSchema: POOL_SCHEMA,
                handler: async (ctx) => {
                    const repo = repoOf(ctx);
                    const path = files(repo).state;
                    const state = { ...(await readJson(path, {})), ...ctx.input, reported: new Date().toISOString() };
                    await writeJson(path, state);
                    return summary(await refresh(repo));
                },
            },
            {
                name: "read_board",
                description: "What the board shows now: the crews' states and what waits for the user.",
                inputSchema: { type: "object", properties: {}, additionalProperties: false },
                handler: async (ctx) => {
                    const item = await entry(repoOf(ctx));
                    return { ...summary(item),
                        crews: (item.snapshot?.crews || []).map(({ name, state, issue, stuck }) => ({ name, state, issue, stuck })),
                        waiting: item.snapshot?.waiting || [] };
                },
            },
        ],
        open: async (ctx) => {
            let instance = instances.get(ctx.instanceId);
            const repo = await resolveRepo(ctx.input);
            if (instance && instance.repo !== repo) {
                instances.delete(ctx.instanceId);
                await instance.server.close();
                instance = null;
            }
            if (!instance) {
                instance = { repo, server: await startServer((request) => route(repo, request)) };
                instances.set(ctx.instanceId, instance);
            }
            const item = await entry(repo);
            if (!item.timer) {
                item.timer = setInterval(() => refresh(repo), EVERY);
                item.timer.unref?.();
            }
            refresh(repo);
            return { title: `Orchi board · ${repo}`, url: instance.server.url };
        },
        onClose: async (ctx) => {
            const instance = instances.get(ctx.instanceId);
            if (!instance) return;
            instances.delete(ctx.instanceId);
            await instance.server.close();
            if (![...instances.values()].some((other) => other.repo === instance.repo)) {
                clearInterval(repos.get(instance.repo)?.timer);
                repos.delete(instance.repo);
            }
        },
    });
}
