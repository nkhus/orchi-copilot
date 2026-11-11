// The design board: rounds of design variants the user sees side by side, scores 1 to 5, notes, and picks. The
// session publishes each round's files under the worktree's `.orchi-tmp/board/v/<round>/` and reads the ratings back.
import { readFile, stat } from "node:fs/promises";
import { extname, isAbsolute, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { CanvasError, createCanvas } from "@github/copilot-sdk/extension";
import { designDone } from "./requests.mjs";
import { checkRound, picks, rate, TYPES, upsertRound, variantPath } from "./rounds.mjs";
import { RequestError, startServer } from "./server.mjs";
import { readJson, writeJson } from "./store.mjs";

const PAGE = fileURLToPath(new URL("../ui/design-board.html", import.meta.url));

const ROUND_SCHEMA = {
    type: "object",
    required: ["id", "title", "items"],
    additionalProperties: false,
    properties: {
        id: { type: "string", description: "Round id, a slug such as `r1-directions`; its files sit under v/<id>/." },
        title: { type: "string", description: "What the round compares, in the user's words." },
        question: { type: "string", description: "What to look at and decide." },
        items: {
            type: "array",
            minItems: 1,
            items: {
                type: "object",
                required: ["id", "file", "label"],
                additionalProperties: false,
                properties: {
                    id: { type: "string", description: "Item id, a slug unique in the round." },
                    file: { type: "string", description: "Path relative to .orchi-tmp/board/, under v/<round>/." },
                    label: { type: "string", description: "The direction, never the skill that made it." },
                    notes: { type: "string" },
                },
            },
        },
    },
};

export function designBoardCanvas(host) {
    const instances = new Map(); // instanceId → { base, server }

    const paths = (base) => ({ rounds: join(base, "rounds.json"), ratings: join(base, "ratings.json") });
    const load = async (base) => ({
        board: await readJson(paths(base).rounds, { product: "", rounds: [] }),
        ratings: await readJson(paths(base).ratings, {}),
    });

    function push(base, event) {
        for (const instance of instances.values()) if (instance.base === base) instance.server.push(event);
    }

    function baseOf(ctx) {
        const instance = instances.get(ctx.instanceId);
        if (!instance) throw new CanvasError("not_open", "Open the design board first.");
        return instance.base;
    }

    async function route(base, { method, path, body }) {
        if (method === "GET" && path === "/") return { type: "text/html; charset=utf-8", data: await readFile(PAGE, "utf8") };
        if (method === "GET" && path.startsWith("/v/")) {
            let file;
            try {
                file = path.slice(1).split("/").map(decodeURIComponent).join("/");
            } catch {
                throw new RequestError("Bad path");
            }
            const real = await variantPath(base, file);
            return { type: TYPES[extname(real).toLowerCase()], data: await readFile(real) };
        }
        const { board, ratings } = await load(base);
        if (method === "GET" && path === "/data") return { json: { product: board.product, rounds: board.rounds, ratings } };
        if (method === "POST" && path === "/rate") {
            const next = rate(ratings, board.rounds, body || {});
            await writeJson(paths(base).ratings, next);
            push(base, { type: "ratings" });
            return { json: next[body.round] };
        }
        if (method === "POST" && path === "/done") {
            const round = board.rounds.find((other) => other.id === body?.round);
            if (!round) throw new RequestError("Unknown round", 404);
            const next = structuredClone(ratings);
            (next[round.id] ||= { done: false, items: {} }).done = true;
            await writeJson(paths(base).ratings, next);
            push(base, { type: "ratings" });
            await host.session.send({ prompt: designDone(round.title) });
            return { json: { done: true } };
        }
        return null;
    }

    return createCanvas({
        id: "orchi-design-board",
        displayName: "Design board",
        description:
            "Orchi's design board: rounds of design variants from .orchi-tmp/board/ that the user compares, scores " +
            "1 to 5, notes, and picks. Publish a round with publish_round; read the ratings with read_picks.",
        inputSchema: {
            type: "object",
            additionalProperties: false,
            properties: {
                root: { type: "string", description: "Absolute path of the worktree; defaults to this session's folder." },
                product: { type: "string", description: "The product's name, shown as the board's title." },
            },
        },
        actions: [
            {
                name: "publish_round",
                description:
                    "Show a round of variants. Put its files under .orchi-tmp/board/v/<id>/ first. Publishing an id " +
                    "again replaces that round and asks the user to rate it again.",
                inputSchema: ROUND_SCHEMA,
                handler: async (ctx) => {
                    const base = baseOf(ctx);
                    const round = await checkRound(base, ctx.input);
                    const { board, ratings } = await load(base);
                    board.rounds = upsertRound(board.rounds, round);
                    await writeJson(paths(base).rounds, board);
                    if (ratings[round.id]) {
                        ratings[round.id].done = false;
                        await writeJson(paths(base).ratings, ratings);
                    }
                    push(base, { type: "rounds", round: round.id });
                    return { round: round.id, items: round.items.length, rounds: board.rounds.length };
                },
            },
            {
                name: "read_picks",
                description:
                    "Read the user's ratings: per round, whether they said they are done, the picked items, and each " +
                    "item's score (1 to 5 or null), note, and pick.",
                inputSchema: {
                    type: "object",
                    additionalProperties: false,
                    properties: { round: { type: "string", description: "One round id; all rounds when omitted." } },
                },
                handler: async (ctx) => {
                    const { board, ratings } = await load(baseOf(ctx));
                    return { rounds: picks(board.rounds, ratings, ctx.input?.round) };
                },
            },
        ],
        open: async (ctx) => {
            const root = ctx.input?.root || process.cwd();
            if (!isAbsolute(root) || !(await stat(root).catch(() => null))?.isDirectory()) {
                throw new CanvasError("bad_root", "root must be the absolute path of an existing folder.");
            }
            const base = resolve(root, ".orchi-tmp", "board");
            let instance = instances.get(ctx.instanceId);
            if (instance && instance.base !== base) {
                instances.delete(ctx.instanceId);
                await instance.server.close();
                instance = null;
            }
            if (!instance) {
                instance = { base, server: await startServer((request) => route(base, request)) };
                instances.set(ctx.instanceId, instance);
            }
            const { board } = await load(base);
            if (ctx.input?.product && ctx.input.product !== board.product) {
                board.product = ctx.input.product;
                await writeJson(paths(base).rounds, board);
            }
            return { title: board.product ? `${board.product} · design board` : "Design board", url: instance.server.url };
        },
        onClose: async (ctx) => {
            const instance = instances.get(ctx.instanceId);
            if (!instance) return;
            instances.delete(ctx.instanceId);
            await instance.server.close();
        },
    });
}
