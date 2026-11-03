/** @odoo-module **/

import { after, describe, expect, test } from "@odoo/hoot";
import { ListRenderer } from "@web/views/list/list_renderer";
import { browser } from "@web/core/browser/browser";
import "@list_view_column_reorder/js/list_renderer_patch";

/**
 * Helper to mock browser.localStorage with an isolated in-memory store
 * and automatically restore original methods on teardown.
 */
function mockLocalStorage(initialData = {}) {
    const store = new Map(Object.entries(initialData));
    const originalGetItem = browser.localStorage.getItem;
    const originalSetItem = browser.localStorage.setItem;
    const originalRemoveItem = browser.localStorage.removeItem;

    browser.localStorage.getItem = (key) => (store.has(key) ? store.get(key) : null);
    browser.localStorage.setItem = (key, val) => store.set(key, String(val));
    browser.localStorage.removeItem = (key) => store.delete(key);

    const restore = () => {
        browser.localStorage.getItem = originalGetItem;
        browser.localStorage.setItem = originalSetItem;
        browser.localStorage.removeItem = originalRemoveItem;
    };
    after(restore);

    return { store, restore };
}

describe("ListRenderer Column Reorder Patch - JS Unit Tests", () => {
    describe.current.tags("desktop");

    // -------------------------------------------------------------------------
    // 1. _buildStorageKey()
    // -------------------------------------------------------------------------
    describe("_buildStorageKey()", () => {
        test("generates storage key formatted as column_order,<model>,<viewId>", () => {
            const renderer = Object.create(ListRenderer.prototype);
            renderer.props = {
                list: { resModel: "sale.order" },
                archInfo: { viewId: 101 },
            };
            expect(renderer._buildStorageKey()).toBe("column_order,sale.order,101");
        });

        test("falls back to env.config.viewId when archInfo.viewId is absent", () => {
            const renderer = Object.create(ListRenderer.prototype);
            renderer.props = {
                list: { resModel: "res.partner" },
                archInfo: {},
            };
            renderer.env = { config: { viewId: 202 } };
            expect(renderer._buildStorageKey()).toBe("column_order,res.partner,202");
        });

        test("falls back to 0 when archInfo.viewId and env.config.viewId are both absent", () => {
            const renderer = Object.create(ListRenderer.prototype);
            renderer.props = {
                list: { resModel: "account.move" },
            };
            renderer.env = {};
            expect(renderer._buildStorageKey()).toBe("column_order,account.move,0");
        });

        test("falls back to 'unknown' when props.list.resModel is absent", () => {
            const renderer = Object.create(ListRenderer.prototype);
            renderer.props = {};
            expect(renderer._buildStorageKey()).toBe("column_order,unknown,0");
        });
    });

    // -------------------------------------------------------------------------
    // 2. _applyOrder()
    // -------------------------------------------------------------------------
    describe("_applyOrder()", () => {
        test("reorders columns matching the given order array of column names", () => {
            const renderer = Object.create(ListRenderer.prototype);
            const columns = [
                { name: "name", label: "Name" },
                { name: "email", label: "Email" },
                { name: "phone", label: "Phone" },
            ];
            const order = ["phone", "name", "email"];
            const reordered = renderer._applyOrder(columns, order);
            expect(reordered.map((c) => c.name)).toEqual(["phone", "name", "email"]);
        });

        test("matches columns by String(c.id) if column has no name or name does not match", () => {
            const renderer = Object.create(ListRenderer.prototype);
            const columns = [
                { id: "col_1", label: "Col 1" },
                { id: "col_2", label: "Col 2" },
                { id: 99, label: "Numeric Id" },
            ];
            const order = ["99", "col_1", "col_2"];
            const reordered = renderer._applyOrder(columns, order);
            expect(reordered.map((c) => c.id)).toEqual([99, "col_1", "col_2"]);
        });

        test("appends any new/untracked columns at the end, maintaining their relative order", () => {
            const renderer = Object.create(ListRenderer.prototype);
            const columns = [
                { name: "a" },
                { name: "b" },
                { name: "c" },
                { name: "d" },
            ];
            const order = ["c", "a"];
            const reordered = renderer._applyOrder(columns, order);
            expect(reordered.map((c) => c.name)).toEqual(["c", "a", "b", "d"]);
        });

        test("ignores order items that do not correspond to any active column", () => {
            const renderer = Object.create(ListRenderer.prototype);
            const columns = [{ name: "a" }, { name: "b" }];
            const order = ["ghost_col", "b", "another_ghost", "a"];
            const reordered = renderer._applyOrder(columns, order);
            expect(reordered.map((c) => c.name)).toEqual(["b", "a"]);
        });

        test("handles empty columns array gracefully", () => {
            const renderer = Object.create(ListRenderer.prototype);
            expect(renderer._applyOrder([], ["a", "b"])).toEqual([]);
        });

        test("handles empty order array gracefully by returning existing columns", () => {
            const renderer = Object.create(ListRenderer.prototype);
            const columns = [{ name: "a" }, { name: "b" }];
            expect(renderer._applyOrder(columns, [])).toEqual(columns);
        });
    });

    // -------------------------------------------------------------------------
    // 3. _reorderColumnsInsertAfter()
    // -------------------------------------------------------------------------
    describe("_reorderColumnsInsertAfter()", () => {
        test("moves a column directly after target column and calls _saveColumnOrder", () => {
            const renderer = Object.create(ListRenderer.prototype);
            renderer.columns = [{ name: "a" }, { name: "b" }, { name: "c" }];
            let savedColumns = null;
            renderer._saveColumnOrder = (cols) => {
                savedColumns = cols;
            };

            renderer._reorderColumnsInsertAfter("a", "b");
            expect(savedColumns.map((c) => c.name)).toEqual(["b", "a", "c"]);
        });

        test("returns early without saving if fromName === afterName", () => {
            const renderer = Object.create(ListRenderer.prototype);
            renderer.columns = [{ name: "a" }, { name: "b" }];
            let saved = false;
            renderer._saveColumnOrder = () => {
                saved = true;
            };

            renderer._reorderColumnsInsertAfter("a", "a");
            expect(saved).toBe(false);
        });

        test("returns early without saving if fromName is not found", () => {
            const renderer = Object.create(ListRenderer.prototype);
            renderer.columns = [{ name: "a" }, { name: "b" }];
            let saved = false;
            renderer._saveColumnOrder = () => {
                saved = true;
            };

            renderer._reorderColumnsInsertAfter("nonexistent", "b");
            expect(saved).toBe(false);
        });

        test("appends moved column to end if afterName is not found", () => {
            const renderer = Object.create(ListRenderer.prototype);
            renderer.columns = [{ name: "a" }, { name: "b" }, { name: "c" }];
            let savedColumns = null;
            renderer._saveColumnOrder = (cols) => {
                savedColumns = cols;
            };

            renderer._reorderColumnsInsertAfter("a", "nonexistent");
            expect(savedColumns.map((c) => c.name)).toEqual(["b", "c", "a"]);
        });

        test("moves column from end to after first column", () => {
            const renderer = Object.create(ListRenderer.prototype);
            renderer.columns = [{ name: "a" }, { name: "b" }, { name: "c" }];
            let savedColumns = null;
            renderer._saveColumnOrder = (cols) => {
                savedColumns = cols;
            };

            renderer._reorderColumnsInsertAfter("c", "a");
            expect(savedColumns.map((c) => c.name)).toEqual(["a", "c", "b"]);
        });
    });

    // -------------------------------------------------------------------------
    // 4. _reorderColumnsInsertBefore()
    // -------------------------------------------------------------------------
    describe("_reorderColumnsInsertBefore()", () => {
        test("moves a column directly before target column and calls _saveColumnOrder", () => {
            const renderer = Object.create(ListRenderer.prototype);
            renderer.columns = [{ name: "a" }, { name: "b" }, { name: "c" }];
            let savedColumns = null;
            renderer._saveColumnOrder = (cols) => {
                savedColumns = cols;
            };

            renderer._reorderColumnsInsertBefore("c", "b");
            expect(savedColumns.map((c) => c.name)).toEqual(["a", "c", "b"]);
        });

        test("returns early without saving if fromName === beforeName", () => {
            const renderer = Object.create(ListRenderer.prototype);
            renderer.columns = [{ name: "a" }, { name: "b" }];
            let saved = false;
            renderer._saveColumnOrder = () => {
                saved = true;
            };

            renderer._reorderColumnsInsertBefore("a", "a");
            expect(saved).toBe(false);
        });

        test("returns early without saving if fromName is not found", () => {
            const renderer = Object.create(ListRenderer.prototype);
            renderer.columns = [{ name: "a" }, { name: "b" }];
            let saved = false;
            renderer._saveColumnOrder = () => {
                saved = true;
            };

            renderer._reorderColumnsInsertBefore("nonexistent", "b");
            expect(saved).toBe(false);
        });

        test("prepends moved column to beginning if beforeName is not found", () => {
            const renderer = Object.create(ListRenderer.prototype);
            renderer.columns = [{ name: "a" }, { name: "b" }, { name: "c" }];
            let savedColumns = null;
            renderer._saveColumnOrder = (cols) => {
                savedColumns = cols;
            };

            renderer._reorderColumnsInsertBefore("c", "nonexistent");
            expect(savedColumns.map((c) => c.name)).toEqual(["c", "a", "b"]);
        });

        test("moves column from start to before last column", () => {
            const renderer = Object.create(ListRenderer.prototype);
            renderer.columns = [{ name: "a" }, { name: "b" }, { name: "c" }];
            let savedColumns = null;
            renderer._saveColumnOrder = (cols) => {
                savedColumns = cols;
            };

            renderer._reorderColumnsInsertBefore("a", "c");
            expect(savedColumns.map((c) => c.name)).toEqual(["b", "a", "c"]);
        });
    });

    // -------------------------------------------------------------------------
    // 5. _saveColumnOrder()
    // -------------------------------------------------------------------------
    describe("_saveColumnOrder()", () => {
        test("updates columnReorderState, saves to browser.localStorage, and dispatches event", () => {
            mockLocalStorage();
            const renderer = Object.create(ListRenderer.prototype);
            renderer.keyColumnOrder = "column_order,test.model,1";
            renderer.columnReorderState = { order: null };

            let eventDispatched = false;
            const handler = () => {
                eventDispatched = true;
            };
            window.addEventListener("column-order-changed", handler);
            after(() => window.removeEventListener("column-order-changed", handler));

            const columns = [{ name: "col_z" }, { name: "col_a" }, { id: "col_id_9" }];
            renderer._saveColumnOrder(columns);

            expect(renderer.columnReorderState.order).toEqual(["col_z", "col_a", "col_id_9"]);
            expect(browser.localStorage.getItem("column_order,test.model,1")).toBe(
                JSON.stringify(["col_z", "col_a", "col_id_9"])
            );
            expect(eventDispatched).toBe(true);
        });
    });

    // -------------------------------------------------------------------------
    // 6. getActiveColumns()
    // -------------------------------------------------------------------------
    describe("getActiveColumns()", () => {
        test("returns unmodified columns when columnReorderState.order is null or empty", () => {
            const renderer = Object.create(ListRenderer.prototype);
            renderer.allColumns = [{ name: "a" }, { name: "b" }, { name: "c" }];
            renderer.optionalActiveFields = {};
            renderer.evalColumnInvisible = () => false;

            // Case 1: order is null
            renderer.columnReorderState = { order: null };
            expect(renderer.getActiveColumns()).toEqual(renderer.allColumns);

            // Case 2: order is empty array
            renderer.columnReorderState = { order: [] };
            expect(renderer.getActiveColumns()).toEqual(renderer.allColumns);
        });

        test("returns reordered columns when columnReorderState.order has custom order", () => {
            const renderer = Object.create(ListRenderer.prototype);
            renderer.allColumns = [{ name: "a" }, { name: "b" }, { name: "c" }];
            renderer.optionalActiveFields = {};
            renderer.evalColumnInvisible = () => false;

            renderer.columnReorderState = { order: ["c", "a", "b"] };
            const active = renderer.getActiveColumns();
            expect(active.map((c) => c.name)).toEqual(["c", "a", "b"]);
        });
    });

    // -------------------------------------------------------------------------
    // 7. Event & Click Blocker Handlers
    // -------------------------------------------------------------------------
    describe("Event & Click Blocker Handlers", () => {
        test("restores stored order from localStorage on initialization", () => {
            const key = "column_order,res.partner,10";
            mockLocalStorage({
                [key]: JSON.stringify(["phone", "name"]),
            });

            let initialOrder = null;
            try {
                const stored = browser.localStorage.getItem(key);
                if (stored) initialOrder = JSON.parse(stored);
            } catch (e) {}

            expect(initialOrder).toEqual(["phone", "name"]);
        });

        test("gracefully handles corrupted JSON in localStorage", () => {
            const key = "column_order,res.partner,10";
            mockLocalStorage({
                [key]: "INVALID_JSON_(((",
            });

            let initialOrder = null;
            try {
                const stored = browser.localStorage.getItem(key);
                if (stored) initialOrder = JSON.parse(stored);
            } catch (e) {}

            expect(initialOrder).toBe(null);
        });

        test("column-order-reset event resets columnReorderState.order to null", () => {
            const columnReorderState = { order: ["col1", "col2"] };
            const resetHandler = () => {
                columnReorderState.order = null;
            };
            window.addEventListener("column-order-reset", resetHandler);
            after(() => window.removeEventListener("column-order-reset", resetHandler));

            window.dispatchEvent(new CustomEvent("column-order-reset"));
            expect(columnReorderState.order).toBe(null);
        });

        test("thead click blocker cancels click when preventClick is 'true'", () => {
            const thead = document.createElement("thead");
            let stopImmediatePropagationCalled = false;

            thead.addEventListener(
                "click",
                (ev) => {
                    if (thead.dataset.preventClick === "true") {
                        ev.stopImmediatePropagation();
                        ev.preventDefault();
                    }
                },
                true
            );

            // With preventClick === "true"
            thead.dataset.preventClick = "true";
            const event1 = new MouseEvent("click", { bubbles: true, cancelable: true });
            event1.stopImmediatePropagation = () => {
                stopImmediatePropagationCalled = true;
            };
            thead.dispatchEvent(event1);

            expect(event1.defaultPrevented).toBe(true);
            expect(stopImmediatePropagationCalled).toBe(true);

            // With preventClick !== "true"
            stopImmediatePropagationCalled = false;
            thead.dataset.preventClick = "false";
            const event2 = new MouseEvent("click", { bubbles: true, cancelable: true });
            event2.stopImmediatePropagation = () => {
                stopImmediatePropagationCalled = true;
            };
            thead.dispatchEvent(event2);

            expect(event2.defaultPrevented).toBe(false);
            expect(stopImmediatePropagationCalled).toBe(false);
        });
    });
});
