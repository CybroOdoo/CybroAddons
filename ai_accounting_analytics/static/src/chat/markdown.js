import { markup } from "@odoo/owl";

/**
 * Minimal, safe markdown renderer for assistant answers: the text is HTML
 * escaped first, then a small subset is formatted (paragraphs, bullet and
 * numbered lists, headings, bold, italic, inline code). No links or raw HTML
 * are ever produced, so model output cannot inject markup.
 */
function escapeHtml(text) {
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}

function inline(text) {
    return text
        .replace(/`([^`]+)`/g, "<code>$1</code>")
        .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
        .replace(/(^|[^*])\*([^*\s][^*]*)\*/g, "$1<em>$2</em>");
}

export function renderMarkdown(source) {
    const lines = escapeHtml(source || "").split(/\r?\n/);
    const html = [];
    let list = null;
    let paragraph = [];

    const flushParagraph = () => {
        if (paragraph.length) {
            html.push(`<p>${inline(paragraph.join("<br/>"))}</p>`);
            paragraph = [];
        }
    };
    const closeList = () => {
        if (list) {
            html.push(`</${list}>`);
            list = null;
        }
    };

    for (const rawLine of lines) {
        const line = rawLine.trimEnd();
        const bullet = line.match(/^\s*[-*•]\s+(.*)$/);
        const numbered = line.match(/^\s*\d+[.)]\s+(.*)$/);
        const heading = line.match(/^\s*#{1,6}\s+(.*)$/);
        if (bullet || numbered) {
            flushParagraph();
            const tag = bullet ? "ul" : "ol";
            if (list !== tag) {
                closeList();
                html.push(`<${tag}>`);
                list = tag;
            }
            html.push(`<li>${inline((bullet || numbered)[1])}</li>`);
        } else if (heading) {
            flushParagraph();
            closeList();
            html.push(`<p class="fw-bold mb-1">${inline(heading[1])}</p>`);
        } else if (!line.trim()) {
            flushParagraph();
            closeList();
        } else {
            closeList();
            paragraph.push(line);
        }
    }
    flushParagraph();
    closeList();
    return markup(html.join(""));
}
