// Rounds and ratings of the design board, kept in the worktree's `.orchi-tmp/board/`: `rounds.json` holds what the
// session published, `ratings.json` what the user rated. Variant files live under `v/<round>/`.
import { realpath, stat } from "node:fs/promises";
import { extname, isAbsolute, join, relative, resolve, sep } from "node:path";
import { RequestError } from "./server.mjs";

export const ID = /^[a-z0-9][a-z0-9-]{0,63}$/;

export const TYPES = {
    ".html": "text/html; charset=utf-8", ".htm": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8", ".mjs": "text/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8", ".txt": "text/plain; charset=utf-8", ".svg": "image/svg+xml",
    ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif", ".webp": "image/webp",
    ".avif": "image/avif", ".ico": "image/x-icon", ".woff": "font/woff", ".woff2": "font/woff2", ".ttf": "font/ttf",
    ".otf": "font/otf", ".mp4": "video/mp4", ".webm": "video/webm",
};

// The real path of `file` under `base/v/`, or an error when it is missing, of an unknown type, or escapes the folder
// (`..`, an absolute path, or a symbolic link pointing out).
export async function variantPath(base, file) {
    if (typeof file !== "string" || !file || isAbsolute(file) || file.includes("\0")) {
        throw new RequestError("file must be a relative path under v/", 400);
    }
    const root = await realpath(join(base, "v")).catch(() => null);
    if (!root) throw new RequestError("No variants published yet", 404);
    const target = resolve(base, file);
    if (!target.startsWith(resolve(base, "v") + sep)) throw new RequestError("file must stay under v/", 403);
    const real = await realpath(target).catch(() => null);
    if (!real || !real.startsWith(root + sep)) throw new RequestError("Not found", 404);
    if (!(await stat(real)).isFile()) throw new RequestError("Not found", 404);
    if (!TYPES[extname(real).toLowerCase()]) throw new RequestError("Unsupported file type", 415);
    return real;
}

export function relativeFile(base, file) {
    return relative(base, resolve(base, file)).split(sep).join("/");
}

// A validated round, its files normalised to paths relative to the board folder.
export async function checkRound(base, round) {
    if (!ID.test(round.id || "")) throw new RequestError("id must be lowercase letters, digits, and hyphens");
    const seen = new Set();
    const items = [];
    for (const item of round.items || []) {
        if (!ID.test(item.id || "") || seen.has(item.id)) throw new RequestError(`item id ${item.id} must be unique and a slug`);
        seen.add(item.id);
        await variantPath(base, item.file);
        items.push({ id: item.id, file: relativeFile(base, item.file), label: String(item.label || item.id),
            notes: String(item.notes || "") });
    }
    if (!items.length) throw new RequestError("A round needs at least one item");
    return { id: round.id, title: String(round.title || round.id), question: String(round.question || ""), items };
}

// Rounds in publishing order; publishing a round id again replaces it in place.
export function upsertRound(rounds, round) {
    const list = Array.isArray(rounds) ? rounds.filter((other) => other.id !== round.id) : [];
    const index = (rounds || []).findIndex((other) => other.id === round.id);
    if (index >= 0) list.splice(index, 0, round);
    else list.push(round);
    return list;
}

export function rate(ratings, rounds, { round, item, score, note, pick }) {
    const known = rounds.find((other) => other.id === round);
    if (!known || !known.items.some((other) => other.id === item)) throw new RequestError("Unknown round or item", 404);
    if (score !== undefined && score !== null && !(Number.isInteger(score) && score >= 1 && score <= 5)) {
        throw new RequestError("score must be 1 to 5");
    }
    const next = structuredClone(ratings || {});
    const entry = (next[round] ||= { done: false, items: {} });
    const current = entry.items[item] || { score: null, note: "", pick: false };
    if (score !== undefined) current.score = score;
    if (note !== undefined) current.note = String(note).slice(0, 4000);
    if (pick !== undefined) current.pick = !!pick;
    entry.items[item] = current;
    return next;
}

// What the session reads back: each round with every item's score, note, and pick, and whether the user is done.
export function picks(rounds, ratings, id) {
    return (rounds || []).filter((round) => !id || round.id === id).map((round) => {
        const entry = (ratings || {})[round.id] || { done: false, items: {} };
        const items = round.items.map((item) => ({ id: item.id, label: item.label, file: item.file,
            ...(entry.items[item.id] || { score: null, note: "", pick: false }) }));
        return { id: round.id, title: round.title, done: !!entry.done, picked: items.filter((item) => item.pick).map((item) => item.id), items };
    });
}
