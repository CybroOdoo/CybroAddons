/** @odoo-module **/

import { browser } from "@web/core/browser/browser";
import { parseSearchQuery, PATH_KEYS, router } from "@web/core/browser/router";
import { omit } from "@web/core/utils/objects";
import { patch } from "@web/core/utils/patch";
import { isNumeric } from "@web/core/utils/strings";
import { objectToUrlEncodedString } from "@web/core/utils/urls";

// Prefixes should be sorted by desc. length.
export const PREFIXES = ["/info/shared"];

/**
 * @param {{ [key: string]: any }} state
 * @returns {string}
 */
export function stateToUrl(state) {
    let pathname = "/info/shared";
    if (state.article_id) {
        pathname = `/info/shared/${state.article_id}`;
    } else if (state.active_id) {
        pathname = `/info/shared/${state.active_id}`;
    } else if (state.id) {
        pathname = `/info/shared/${state.id}`;
    }
    const search = objectToUrlEncodedString(omit(state, "actionStack", ...PATH_KEYS));
    return `${pathname}${search ? `?${search}` : ""}`;
}

/**
 * @param {URL} urlObj
 * @returns {{ [key: string]: any }}
 */
export function urlToState(urlObj) {
    const { pathname, search } = urlObj;
    const state = parseSearchQuery(search);
    const prefix = PREFIXES.find((prefix) => pathname.startsWith(prefix));
    if (prefix === "/info/shared") {
        const remaining = pathname.replace(prefix, "");
        const splitPath = remaining.split("/").filter(Boolean);
        if (splitPath.length && isNumeric(splitPath[0])) {
            state.article_id = parseInt(splitPath[0]);
            state.active_id = state.article_id;
            state.id = state.article_id;
        }
    }
    return state;
}

patch(router, {
    stateToUrl,
    urlToState,
});

// Since the patch for `stateToUrl` and `urlToState` is executed
// after the router state was already initialized, it has to be replaced.
router.replaceState(router.urlToState(new URL(browser.location)));
