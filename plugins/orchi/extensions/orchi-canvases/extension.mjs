// Orchi's canvases: the board of the pool and the design board. This file only wires them into the session.
import { joinSession } from "@github/copilot-sdk/extension";
import { boardCanvas } from "./lib/board.mjs";
import { designBoardCanvas } from "./lib/design-board.mjs";

// The canvases receive the session once joinSession returns; they use it only after the user opens one.
const host = { session: null };

host.session = await joinSession({ canvases: [boardCanvas(host), designBoardCanvas(host)] });
