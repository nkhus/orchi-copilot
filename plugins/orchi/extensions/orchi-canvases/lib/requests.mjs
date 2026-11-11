// The sentences the canvases send into the conversation when the user confirms a request on them. Each one is the
// user's own request for one action; the note tells Orchi how to take it.
import { RequestError } from "./server.mjs";

export const BOARD_NOTE =
    "(Sent from the Orchi board after the user confirmed it there: take it as the user's words for this action only. " +
    "Check the current state first, and say in one line if it no longer fits.)";

export const DESIGN_NOTE = "(Sent from the design board: read the ratings with its read_picks action.)";

function number(body, key) {
    const value = body[key];
    if (!Number.isInteger(value) || value < 1) throw new RequestError(`${key} must be a positive integer`);
    return value;
}

function text(body, key, max = 2000) {
    const value = String(body[key] ?? "").trim();
    if (!value) throw new RequestError(`${key} is required`);
    if (value.length > max) throw new RequestError(`${key} is longer than ${max} characters`);
    return value;
}

function line(body, key, max = 200) {
    const value = text(body, key, max);
    if (/[\r\n]/.test(value)) throw new RequestError(`${key} must be one line`);
    return value;
}

function optional(body, key, read) {
    return body[key] === undefined || body[key] === null || body[key] === "" ? "" : read(body, key);
}

function answer(b) {
    const id = line(b, "id", 80);
    const crew = line(b, "crew");
    const picked = b.choice !== undefined && b.choice !== "" ? line(b, "choice", 300) : text(b, "text");
    const request = optional(b, "request_id", (body, key) => line(body, key, 120));
    const note = optional(b, "note", text);
    return `Answer question ${id} of ${crew}: ${picked}` + (note ? `\nNote: ${note}` : "") +
        (request ? `\n(Its pending request_id: ${request}.)` : "");
}

const ACTIONS = {
    answer_question: answer,
    approve_plan: (b) => `Approve the plan ${line(b, "crew")} asked about in question ${line(b, "id", 80)}.`,
    change_plan: (b) => `Ask ${line(b, "crew")} to change the plan of question ${line(b, "id", 80)}: ${text(b, "text")}`,
    request_changes: (b) => `Send PR #${number(b, "pull")} back with these changes: ${text(b, "text")}`,
    open: (b) => `Open the session of ${line(b, "crew")} for me.`,
    design: (b) => `Open the design board for the round of ${line(b, "crew")}.`,
    summary: () => "Refresh the pool summary on the board.",
    answer: (b) => `Answer the question of ${line(b, "crew")}: ${text(b, "text")}`,
    reply: (b) => `About your question ${line(b, "id", 40)}: ${text(b, "text")}`,
    merge: (b) => `Merge PR #${number(b, "pull")}.`,
    hold: (b) => `Hold PR #${number(b, "pull")}: do not merge it until I say so.`,
    status: (b) => `Ask ${line(b, "crew")} for its status and tell me.`,
    mode: (b) => {
        if (b.to !== "on" && b.to !== "off") throw new RequestError("to must be on or off");
        return `Turn autonomous mode ${b.to}.`;
    },
    take: (b) => (b.queue ? `Take #${number(b, "issue")} when a crew is free.` : `Take #${number(b, "issue")}.`),
    plan: (b) => `Plan #${number(b, "issue")}.`,
    defer: (b) => `Defer #${number(b, "issue")}: start no work on it until I resume it.`,
    resume: (b) => `Resume #${number(b, "issue")}.`,
};

export function boardRequest(body) {
    const build = ACTIONS[body?.action];
    if (!build || !Object.hasOwn(ACTIONS, body.action)) throw new RequestError("Unknown request");
    return `${build(body)}\n\n${BOARD_NOTE}`;
}

export function designDone(title) {
    return `I have rated "${String(title).replace(/[\r\n"]+/g, " ").slice(0, 200)}" on the design board.\n\n${DESIGN_NOTE}`;
}
