import { isMacOS } from "@web/core/browser/feature_detection";
import { fuzzyLookup } from "@web/core/utils/search";

/**
 * Menus as searchable entries, and the helpers the menu search and the app
 * board share to rank, link, draw and highlight them.
 */

export const MENU_SEARCH_HOTKEY = "control+shift+f";
export const MENU_SEARCH_SHORTCUT_LABEL = isMacOS() ? "⌘ ⇧ F" : "Ctrl ⇧ F";

const RESULT_LIMIT = 50;

/** Lower case, without accents: "Créer" matches "creer". */
function normalizeChar(char) {
    return char.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
}

export function normalize(str) {
    return Array.from(str || "", normalizeChar).join("");
}

/**
 * Flattens the menu tree into searchable entries: every menu that opens an
 * action, with the names of its ancestors as a breadcrumb path.
 * The menus service only returns menus the user has access to.
 */
export function buildMenuIndex(menuService) {
    const entries = [];
    const visit = (menuId, path, app) => {
        const menu = menuService.getMenu(menuId);
        if (!menu) {
            return;
        }
        const currentApp = app || menu;
        if (menu.actionID) {
            entries.push({
                id: menu.id,
                menu,
                name: menu.name,
                app: currentApp,
                path,
                pathLabel: path.join(" / "),
                haystack: normalize([...path, menu.name].join(" ")),
                nameKey: normalize(menu.name),
            });
        }
        for (const childId of menu.children || []) {
            visit(childId, [...path, menu.name], currentApp);
        }
    };
    for (const app of menuService.getApps()) {
        visit(app.id, [], null);
    }
    return entries;
}

/**
 * Every word of the query must appear in the entry's name or path. Names
 * starting with the query rank first, then names containing it, then
 * matches on the path only. Falls back to fuzzy matching on typos: those
 * results are flagged with `fuzzy`, as they are only lookalikes.
 */
export function searchMenus(entries, query) {
    const q = normalize(query).trim();
    if (!q) {
        return [];
    }
    const words = q.split(/\s+/);
    const scored = [];
    for (const entry of entries) {
        if (!words.every((w) => entry.haystack.includes(w))) {
            continue;
        }
        let score = 3;
        if (entry.nameKey.startsWith(q)) {
            score = 0;
        } else if (entry.nameKey.includes(q)) {
            score = 1;
        } else if (words.some((w) => entry.nameKey.includes(w))) {
            score = 2;
        }
        scored.push({ entry, score });
    }
    if (!scored.length) {
        const lookalikes = fuzzyLookup(q, entries, (e) => e.haystack).slice(0, RESULT_LIMIT);
        lookalikes.fuzzy = true;
        return lookalikes;
    }
    scored.sort(
        (a, b) =>
            a.score - b.score ||
            a.entry.path.length - b.entry.path.length ||
            a.entry.name.localeCompare(b.entry.name)
    );
    return scored.slice(0, RESULT_LIMIT).map((s) => s.entry);
}

/** How to draw an app's icon: its image, its icon font glyph, or its initial. */
export function appIcon(app) {
    if (app.webIconData) {
        return { type: "img", src: app.webIconData };
    }
    if (app.webIcon && !app.webIcon.includes("/")) {
        const [iconClass, color, background] = app.webIcon.split(",");
        return { type: "icon", iconClass, color, background };
    }
    return { type: "letter", letter: (app.name || "?").charAt(0).toUpperCase() };
}

/**
 * Splits a label into [{text, match}] chunks so the words of the query can
 * be highlighted in a template without injecting markup. Matching ignores
 * case and accents, character by character, so the highlighted parts stay
 * aligned with the label even when an accented letter normalizes to more
 * or fewer characters.
 */
export function highlightChunks(label, query) {
    const words = normalize(query).trim().split(/\s+/).filter(Boolean);
    const chars = Array.from(label || "");
    if (!words.length) {
        return [{ text: chars.join(""), match: false }];
    }
    // The normalized label, and for each of its positions the label character
    // it comes from.
    let norm = "";
    const source = [];
    chars.forEach((char, index) => {
        const normalized = normalizeChar(char);
        norm += normalized;
        source.push(...Array(normalized.length).fill(index));
    });
    const marks = new Array(chars.length).fill(false);
    for (const word of words) {
        for (let i = norm.indexOf(word); i !== -1; i = norm.indexOf(word, i + word.length)) {
            for (let k = i; k < i + word.length; k++) {
                marks[source[k]] = true;
            }
        }
    }
    const chunks = [];
    chars.forEach((char, index) => {
        const last = chunks.at(-1);
        if (last && last.match === marks[index]) {
            last.text += char;
        } else {
            chunks.push({ text: char, match: marks[index] });
        }
    });
    return chunks;
}

/** Link of a menu, as the top bar builds it. */
export function menuHref(menu) {
    return `/odoo/${menu.actionPath || "action-" + menu.actionID}`;
}
