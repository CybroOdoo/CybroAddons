/**
 * POST a question and iterate (``for await``) over the newline-delimited JSON
 * events streamed back by the server (see controllers/chat.py).
 *
 * @param {Object} params form fields sent with the question
 * @param {AbortSignal} signal aborts the request (stop button)
 * @returns {AsyncGenerator<Object>}
 */
export function streamChat(params, signal) {
    // Odoo's module transpiler does not support exported generators.
    return readEvents(params, signal);
}

async function* readEvents(params, signal) {
    const body = new FormData();
    body.append("csrf_token", odoo.csrf_token);
    for (const [key, value] of Object.entries(params)) {
        if (value !== undefined && value !== null && value !== false) {
            body.append(key, value);
        }
    }
    const response = await fetch("/ai_accounting_analytics/chat/stream", {
        method: "POST",
        body,
        signal,
    });
    if (!response.ok || !response.body) {
        throw new Error(`HTTP ${response.status}`);
    }
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    while (true) {
        const { value, done } = await reader.read();
        if (done) {
            break;
        }
        buffer += decoder.decode(value, { stream: true });
        let newline;
        while ((newline = buffer.indexOf("\n")) >= 0) {
            const line = buffer.slice(0, newline).trim();
            buffer = buffer.slice(newline + 1);
            if (line) {
                yield JSON.parse(line);
            }
        }
    }
    if (buffer.trim()) {
        yield JSON.parse(buffer);
    }
}
