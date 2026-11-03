/** @odoo-module */

import { expect, test } from "@odoo/hoot";
import { WarningDialog } from "@web/core/errors/error_dialogs";
import { translatedTerms, translationLoaded } from "@web/core/l10n/translation";
import { GoogleSearchWidget } from "@google_search_in_odoo/js/google_search";

/**
 * _t() returns a lazy string until translations are loaded.
 * Bare unit tests do not load translation bundles, so we flip the flag for the call.
 */
async function withTranslationsLoaded(callback) {
    const original = translatedTerms[translationLoaded];
    translatedTerms[translationLoaded] = true;
    try {
        return await callback();
    } finally {
        translatedTerms[translationLoaded] = original;
    }
}

function makeContext(ormResult, initialQuery = "odoo") {
    const dialogCalls = [];
    const state = {
        isGoogleSearchEnabled: false,
        showResults: false,
        query: initialQuery,
        results: [],
        expandedIndices: {},
    };

    const context = {
        state,
        orm: {
            call: async () => ormResult,
        },
        dialog: {
            add: (component, props) => dialogCalls.push({ component, props }),
        },
    };

    return { context, dialogCalls, state };
}

test("onKeyPress triggers a search only on Enter", () => {
    let searchCalled = false;
    const context = { _onSearch: () => { searchCalled = true; } };

    let prevented = false;
    const enterEv = { key: "Enter", preventDefault: () => { prevented = true; } };
    GoogleSearchWidget.prototype.onKeyPress.call(context, enterEv);

    expect(prevented).toBe(true);
    expect(searchCalled).toBe(true);

    searchCalled = false;
    const otherEv = { key: "a", preventDefault: () => { throw new Error("should not be called"); } };
    GoogleSearchWidget.prototype.onKeyPress.call(context, otherEv);

    expect(searchCalled).toBe(false);
});

test("_onCloseResults hides the results panel and stops propagation", () => {
    let stopped = false;
    const ev = { stopPropagation: () => { stopped = true; } };
    const context = {
        state: { showResults: true },
    };

    GoogleSearchWidget.prototype._onCloseResults.call(context, ev);

    expect(stopped).toBe(true);
    expect(context.state.showResults).toBe(false);
});

test("toggleExpand toggles the expanded state for an index", () => {
    const context = {
        state: { expandedIndices: {} },
    };

    GoogleSearchWidget.prototype.toggleExpand.call(context, 0);
    expect(context.state.expandedIndices[0]).toBe(true);

    GoogleSearchWidget.prototype.toggleExpand.call(context, 0);
    expect(context.state.expandedIndices[0]).toBe(false);
});

test("_checkSearchStatus updates isGoogleSearchEnabled from res.users", async () => {
    const { context, state } = makeContext(true);

    await GoogleSearchWidget.prototype._checkSearchStatus.call(context);
    expect(state.isGoogleSearchEnabled).toBe(true);
});

test("_onSearch hides results panel when query is empty", async () => {
    const { context, state } = makeContext([], "   ");
    state.showResults = true;

    await GoogleSearchWidget.prototype._onSearch.call(context);
    expect(state.showResults).toBe(false);
});

test("_onSearch shows a warning dialog when server returns an error", async () => {
    const { context, dialogCalls } = makeContext({ error: "Please enable Google Search." });

    await withTranslationsLoaded(async () => {
        await GoogleSearchWidget.prototype._onSearch.call(context);
    });

    expect(dialogCalls.length).toBe(1);
    expect(dialogCalls[0].component).toBe(WarningDialog);
    expect(String(dialogCalls[0].props.title)).toBe("Alert");
    expect(String(dialogCalls[0].props.message)).toBe("Please enable Google Search.");
});

test("_onSearch shows a warning dialog when server returns null", async () => {
    const { context, dialogCalls } = makeContext(null);

    await withTranslationsLoaded(async () => {
        await GoogleSearchWidget.prototype._onSearch.call(context);
    });

    expect(dialogCalls.length).toBe(1);
    expect(dialogCalls[0].component).toBe(WarningDialog);
    expect(String(dialogCalls[0].props.title)).toBe("Warning");
    expect(String(dialogCalls[0].props.message)).toBe("Limit exceeded for Queries and Queries per day");
});

test("_onSearch updates results in state and displays results panel", async () => {
    const searchResults = [
        { title: "Odoo Official Site", link: "https://www.odoo.com", snippet: "Short snippet" },
        { title: "Odoo Docs", link: "https://www.odoo.com/documentation", snippet: "Another short one" },
    ];
    const { context, state } = makeContext(searchResults);

    await GoogleSearchWidget.prototype._onSearch.call(context);

    expect(state.results.length).toBe(2);
    expect(state.showResults).toBe(true);
    expect(state.results[0].title).toBe("Odoo Official Site");
    expect(state.results[1].link).toBe("https://www.odoo.com/documentation");
});

test("_onSearch handles network/server exceptions cleanly", async () => {
    const dialogCalls = [];
    const context = {
        state: { query: "odoo", showResults: false },
        orm: {
            call: async () => {
                throw new Error("Connection failed");
            },
        },
        dialog: {
            add: (component, props) => dialogCalls.push({ component, props }),
        },
    };

    await withTranslationsLoaded(async () => {
        await GoogleSearchWidget.prototype._onSearch.call(context);
    });

    expect(dialogCalls.length).toBe(1);
    expect(dialogCalls[0].component).toBe(WarningDialog);
    expect(String(dialogCalls[0].props.title)).toBe("Alert");
    expect(String(dialogCalls[0].props.message)).toBe("Unable to perform search. Please try again later.");
});
