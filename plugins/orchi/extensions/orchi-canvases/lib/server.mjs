// A loopback HTTP server per canvas instance. Every URL carries a random token as its first path segment, so other
// local processes and pages cannot read the board or send requests in the user's name, and relative links inside
// served files keep working.
import { createServer } from "node:http";
import { randomBytes } from "node:crypto";

const LIMIT = 64 * 1024;

export class RequestError extends Error {
    constructor(message, status = 400) {
        super(message);
        this.status = status;
    }
}

export async function startServer(route) {
    const token = randomBytes(18).toString("base64url");
    const clients = new Set();
    let port = 0;
    const server = createServer(async (req, res) => {
        try {
            const url = new URL(req.url, "http://127.0.0.1");
            // Reject other hosts (DNS rebinding) and requests without the token.
            if (req.headers.host !== `127.0.0.1:${port}`) return send(res, 403, "text/plain", "Forbidden");
            const [, first, ...rest] = url.pathname.split("/");
            if (first !== token) return send(res, 404, "text/plain", "Not found");
            const path = "/" + rest.join("/");
            if (req.method === "GET" && path === "/events") {
                res.writeHead(200, { "Content-Type": "text/event-stream", "Cache-Control": "no-store", Connection: "keep-alive" });
                res.write(": connected\n\n");
                clients.add(res);
                req.on("close", () => clients.delete(res));
                return;
            }
            let body;
            if (req.method === "POST") {
                if (!String(req.headers["content-type"] || "").startsWith("application/json")) {
                    return send(res, 415, "text/plain", "JSON only");
                }
                body = JSON.parse((await readBody(req)) || "{}");
            } else if (req.method !== "GET") {
                return send(res, 405, "text/plain", "Method not allowed");
            }
            const reply = await route({ method: req.method, path, query: url.searchParams, body });
            if (!reply) return send(res, 404, "text/plain", "Not found");
            return send(res, reply.status || 200, reply.type || "application/json; charset=utf-8",
                reply.data !== undefined ? reply.data : JSON.stringify(reply.json));
        } catch (error) {
            return send(res, error.status || 400, "application/json; charset=utf-8",
                JSON.stringify({ error: String(error.message || error) }));
        }
    });
    await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
    port = server.address().port;
    return {
        url: `http://127.0.0.1:${port}/${token}/`,
        push(event) {
            const line = `data: ${JSON.stringify(event)}\n\n`;
            for (const client of clients) client.write(line);
        },
        close() {
            for (const client of clients) client.end();
            return new Promise((resolve) => server.close(() => resolve()));
        },
    };
}

function send(res, status, type, data) {
    res.writeHead(status, { "Content-Type": type, "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff" });
    res.end(data);
}

function readBody(req) {
    return new Promise((resolve, reject) => {
        let size = 0;
        const chunks = [];
        req.on("data", (chunk) => {
            size += chunk.length;
            if (size > LIMIT) {
                reject(new RequestError("Request too large", 413));
                req.destroy();
            } else chunks.push(chunk);
        });
        req.on("end", () => resolve(Buffer.concat(chunks).toString("utf8")));
        req.on("error", reject);
    });
}
