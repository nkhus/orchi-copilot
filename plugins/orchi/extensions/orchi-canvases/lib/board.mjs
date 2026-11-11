// The Orchi board: the pool's crews and backlog for one repository. Anyone can build it from GitHub through the
// bundled board.py; it changes nothing in GitHub. Where Orchi reports through `update_pool`, it is the owner's board:
// it adds the crews' live state and the user's questions, and a button the user confirms becomes a request in this
// conversation. Everywhere else it is read-only.
import { execFile } from "node:child_process";
import { readFile } from "node:fs/promises";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { CanvasError, createCanvas } from "@github/copilot-sdk/extension";
import { boardRequest } from "./requests.mjs";
import { RequestError, startServer } from "./server.mjs";
import { readJson, sessionFiles, writeJson } from "./store.mjs";

const SCRIPT = fileURLToPath(new URL("../../../skills/orchi-core/scripts/board.py", import.meta.url));
const PAGE = fileURLToPath(new URL("../ui/board.html", import.meta.url));
const REPO = /^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/;
const EVERY = 5 * 60 * 1000;
const STATES = ["working", "waiting", "idle", "stuck", "free"];
const KINDS = ["question", "plan", "permission", "merge", "design"];
const SENT = 50;
const texts = (description) => ({ type: "array", items: { type: "string" }, description });
const object = (properties, required = []) => ({ type: "object", required, additionalProperties: false, properties });

const POOL_SCHEMA = object({
    crews: {
        type: "array",
        description: "Every crew of the pool, as get_sessions_status shows it now.",
        items: object({
            name: { type: "string", description: "The crew's session name, `[<role>] <topic>`." },
            session_id: { type: "string" },
            state: { type: "string", enum: STATES, description: "waiting = needs the user's input." },
            issue: { type: "integer", description: "The Issue it holds, as its assignment names it." },
            doing: { type: "string", description: "What it does now, in a few plain words." },
            question: { type: "string", description: "Its question, while it waits for input." },
            background: { type: "string", description: "Its background run, while it is idle." },
            since: { type: "string", description: "ISO time of its last activity." },
            stuck: { type: "string", description: "Why it is stuck, when Orchi knows." },
            runs: { type: "string", description: "Its model and mode, in a few words." },
            pr: { type: "integer", description: "Its open PR." },
            branch: { type: "string" },
        }, ["name", "state"]),
    },
    mode: { type: "string", enum: ["on", "off"], description: "Autonomous mode." },
    limit: { type: "integer", minimum: 1, description: "How many crews may hold work at once." },
    questions: {
        type: "array",
        description:
            "The user's open questions Orchi keeps in its conversation, with request_id while a crew is blocked on " +
            "ask_user or a plan.",
        items: object({
            id: { type: "string" },
            crew: { type: "string", description: "Who asks: a crew's name, or Orchi." },
            issue: { type: "integer", description: "The Issue or PR it is about." },
            kind: { type: "string", enum: KINDS, description: "permission = a tool approval; only its session answers it." },
            blocking: { type: "boolean", description: "false when the crew goes on with `assumed` meanwhile." },
            assumed: { type: "string", description: "The answer the crew assumes until the user answers." },
            text: { type: "string" },
            context: texts("A few lines the user needs to answer."),
            choices: {
                type: "array",
                items: object({ label: { type: "string" }, detail: { type: "string", description: "Its consequence." },
                    recommended: { type: "boolean" } }, ["label"]),
            },
            plan: texts("A plan's Tasks, when kind is plan."),
            request_id: { type: "string", description: "The exact awaiting_input or pending_plan request_id." },
            links: { type: "array", items: object({ label: { type: "string" }, url: { type: "string" } }, ["url"]) },
            asked: { type: "string", description: "ISO time." },
        }, ["id"]),
    },
    summary: object({
        paragraphs: {
            type: "array",
            description: "Orchi's answer to \"How are things going?\" in a few short paragraphs: what moved forward, " +
                "what is in progress, what is stuck and why (or plainly that nothing is), problems or risks, what " +
                "waits for the user, and what comes next.",
            items: object({
                lead: { type: "string", description: "Its point in one short sentence, shown in bold." },
                text: { type: "string", description: "The rest, naming Issues and PRs as #<n> and crews by name." },
            }, ["text"]),
        },
        since: { type: "string", description: "One line on what changed today: PRs merged, questions answered, Epics closed." },
        at: { type: "string", description: "ISO time." },
    }),
    queue: {
        type: "array",
        description: "Work a planner keeps queued, in order; the board adds the planned work nobody holds after it.",
        items: object({ issue: { type: "integer" }, action: { type: "string", enum: ["take", "plan"] },
            title: { type: "string" }, after: { type: "integer", description: "The Issue it waits for." } }, ["issue"]),
    },
});

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

    // An answer the user sent hides its question until Orchi reports the question answered.
    async function remember(repo, body) {
        const path = files(repo).state;
        const state = await readJson(path, {});
        const entry = { id: String(body.id), crew: String(body.crew), question: String(body.question || "").slice(0, 500),
            answer: String(body.choice || body.text || "").slice(0, 500), at: new Date().toISOString() };
        state.sent = [...(state.sent || []).filter((item) => item.id !== entry.id), entry].slice(-SENT);
        await writeJson(path, state);
        refresh(repo);
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
            if (!(await readJson(files(repo).state, {})).reported) {
                throw new RequestError("This board is read-only: actions happen on the owner's board.", 403);
            }
            const prompt = boardRequest(body);
            await host.session.send({ prompt });
            if (body.action === "answer_question") await remember(repo, body);
            return { json: { sent: prompt } };
        }
        return null;
    }

    return createCanvas({
        id: "orchi-board",
        displayName: "Orchi board",
        description:
            "The Orchi pool of one repository: crews by what needs a look, the Initiative-Epic-Task backlog with PRs " +
            "and checks, and what waits for the user, built from GitHub. Orchi adds its live state with update_pool.",
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
                    "Report what only Orchi knows: the crews as get_sessions_status shows them, the user's open " +
                    "questions, the Summary, autonomous mode, pool size, and the planner's queue. Fields you pass " +
                    "replace the stored ones; then the board refreshes and becomes the owner's board, with actions.",
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
                        waiting: item.snapshot?.waiting || [],
                        questions: (item.snapshot?.questions || []).map(({ id, crew, issue, kind, blocking, request_id }) =>
                            ({ id, crew, issue, kind, blocking, request_id })),
                        answered: item.snapshot?.answered || [] };
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
