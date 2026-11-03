/** @odoo-module **/

import { after, describe, expect, test } from "@odoo/hoot";
import { ListController } from "@web/views/list/list_controller";
import { ListRenderer } from "@web/views/list/list_renderer";
import { browser } from "@web/core/browser/browser";
import "@list_view_column_reorder/js/list_controller_patch";
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

describe("ListController Column Reorder Patch - JS Unit Tests", () => {
    describe.current.tags("desktop");

    // -------------------------------------------------------------------------
    // 1. _buildColumnOrderKey()
    // -------------------------------------------------------------------------
    describe("_buildColumnOrderKey()", () => {
        test("builds key from this.model.root.resModel and this.props.archInfo.viewId", () => {
            const controller = Object.create(ListController.prototype);
            controller.model = { root: { resModel: "project.task" } };
            controller.props = { archInfo: { viewId: 303 } };
            expect(controller._buildColumnOrderKey()).toBe("column_order,project.task,303");
        });

        test("falls back to this.props.resModel when model.root.resModel is absent", () => {
            const controller = Object.create(ListController.prototype);
            controller.model = {};
            controller.props = { resModel: "hr.employee", archInfo: { viewId: 404 } };
            expect(controller._buildColumnOrderKey()).toBe("column_order,hr.employee,404");
        });

        test("falls back to this.env.config.viewId when archInfo.viewId is absent", () => {
            const controller = Object.create(ListController.prototype);
            controller.props = { resModel: "sale.order" };
            controller.env = { config: { viewId: 505 } };
            expect(controller._buildColumnOrderKey()).toBe("column_order,sale.order,505");
        });

        test("falls back to 'unknown' model and 0 viewId when no model or viewId is present", () => {
            const controller = Object.create(ListController.prototype);
            controller.props = {};
            controller.env = {};
            expect(controller._buildColumnOrderKey()).toBe("column_order,unknown,0");
        });
    });

    // -------------------------------------------------------------------------
    // 2. _refreshColumnOrderState()
    // -------------------------------------------------------------------------
    describe("_refreshColumnOrderState()", () => {
        test("sets hasCustomOrder to true when stored order exists in localStorage", () => {
            const key = "column_order,crm.lead,1";
            mockLocalStorage({ [key]: JSON.stringify(["colA", "colB"]) });

            const controller = Object.create(ListController.prototype);
            controller._buildColumnOrderKey = () => key;
            controller.columnOrderState = { hasCustomOrder: false };
            let syncCalled = false;
            controller._syncResetButton = () => {
                syncCalled = true;
            };

            controller._refreshColumnOrderState();
            expect(controller.columnOrderState.hasCustomOrder).toBe(true);
            expect(syncCalled).toBe(true);
        });

        test("sets hasCustomOrder to false when no order exists in localStorage", () => {
            const key = "column_order,crm.lead,1";
            mockLocalStorage({});

            const controller = Object.create(ListController.prototype);
            controller._buildColumnOrderKey = () => key;
            controller.columnOrderState = { hasCustomOrder: true };
            let syncCalled = false;
            controller._syncResetButton = () => {
                syncCalled = true;
            };

            controller._refreshColumnOrderState();
            expect(controller.columnOrderState.hasCustomOrder).toBe(false);
            expect(syncCalled).toBe(true);
        });
    });

    // -------------------------------------------------------------------------
    // 3. _syncResetButton()
    // -------------------------------------------------------------------------
    describe("_syncResetButton()", () => {
        test("returns early without error when rootRef() returns null or undefined", () => {
            const controller = Object.create(ListController.prototype);
            controller.rootRef = () => null;
            controller.columnOrderState = { hasCustomOrder: true };

            expect(() => controller._syncResetButton()).not.toThrow();
        });

        test("removes .o_list_button_reset_columns when hasCustomOrder is false", () => {
            const container = document.createElement("div");
            const btn = document.createElement("button");
            btn.className = "btn btn-secondary o_list_button_reset_columns ms-1";
            container.appendChild(btn);

            const controller = Object.create(ListController.prototype);
            controller.rootRef = () => container;
            controller.columnOrderState = { hasCustomOrder: false };

            controller._syncResetButton();
            expect(container.querySelector(".o_list_button_reset_columns")).toBe(null);
        });

        test("does not add duplicate button if .o_list_button_reset_columns is already present", () => {
            const container = document.createElement("div");
            const addBtn = document.createElement("button");
            addBtn.className = "btn btn-primary o_list_button_add";
            const resetBtn = document.createElement("button");
            resetBtn.className = "btn btn-secondary o_list_button_reset_columns ms-1";
            resetBtn.textContent = "Set Default";
            container.appendChild(addBtn);
            container.appendChild(resetBtn);

            const controller = Object.create(ListController.prototype);
            controller.rootRef = () => container;
            controller.columnOrderState = { hasCustomOrder: true };

            controller._syncResetButton();
            const resetButtons = container.querySelectorAll(".o_list_button_reset_columns");
            expect(resetButtons.length).toBe(1);
        });

        test("does nothing when hasCustomOrder is true but .o_list_button_add is not in DOM", () => {
            const container = document.createElement("div");
            const controller = Object.create(ListController.prototype);
            controller.rootRef = () => container;
            controller.columnOrderState = { hasCustomOrder: true };

            controller._syncResetButton();
            expect(container.querySelector(".o_list_button_reset_columns")).toBe(null);
        });

        test("creates and appends 'Set Default' button right after .o_list_button_add", () => {
            const container = document.createElement("div");
            const addBtn = document.createElement("button");
            addBtn.className = "btn btn-primary o_list_button_add";
            addBtn.textContent = "New";
            const nextSibling = document.createElement("div");
            nextSibling.className = "other-element";
            container.appendChild(addBtn);
            container.appendChild(nextSibling);

            const controller = Object.create(ListController.prototype);
            controller.rootRef = () => container;
            controller.columnOrderState = { hasCustomOrder: true };

            controller._syncResetButton();

            const resetBtn = container.querySelector(".o_list_button_reset_columns");
            expect(resetBtn).not.toBe(null);
            expect(resetBtn.tagName).toBe("BUTTON");
            expect(resetBtn.type).toBe("button");
            expect(resetBtn.textContent).toBe("Set Default");
            expect(resetBtn.title).toBe("Reset column order to Odoo default");
            expect(resetBtn.classList.contains("btn")).toBe(true);
            expect(resetBtn.classList.contains("btn-secondary")).toBe(true);
            expect(resetBtn.classList.contains("ms-1")).toBe(true);

            expect(addBtn.nextElementSibling).toBe(resetBtn);
        });

        test("clicking the generated reset button calls resetColumnOrder()", () => {
            const container = document.createElement("div");
            const addBtn = document.createElement("button");
            addBtn.className = "btn btn-primary o_list_button_add";
            container.appendChild(addBtn);

            let resetCalled = false;
            const controller = Object.create(ListController.prototype);
            controller.rootRef = () => container;
            controller.columnOrderState = { hasCustomOrder: true };
            controller.resetColumnOrder = () => {
                resetCalled = true;
            };

            controller._syncResetButton();

            const resetBtn = container.querySelector(".o_list_button_reset_columns");
            resetBtn.click();
            expect(resetCalled).toBe(true);
        });
    });

    // -------------------------------------------------------------------------
    // 4. resetColumnOrder()
    // -------------------------------------------------------------------------
    describe("resetColumnOrder()", () => {
        test("clears localStorage, resets flag, cleans up button, and dispatches reset event", () => {
            const key = "column_order,sale.order,20";
            mockLocalStorage({ [key]: JSON.stringify(["colB", "colA"]) });

            const container = document.createElement("div");
            const btn = document.createElement("button");
            btn.className = "btn btn-secondary o_list_button_reset_columns ms-1";
            container.appendChild(btn);

            const controller = Object.create(ListController.prototype);
            controller._buildColumnOrderKey = () => key;
            controller.rootRef = () => container;
            controller.columnOrderState = { hasCustomOrder: true };

            let eventDispatched = false;
            const resetListener = () => {
                eventDispatched = true;
            };
            window.addEventListener("column-order-reset", resetListener);
            after(() => window.removeEventListener("column-order-reset", resetListener));

            controller.resetColumnOrder();

            expect(browser.localStorage.getItem(key)).toBe(null);
            expect(controller.columnOrderState.hasCustomOrder).toBe(false);
            expect(container.querySelector(".o_list_button_reset_columns")).toBe(null);
            expect(eventDispatched).toBe(true);
        });
    });

    // -------------------------------------------------------------------------
    // 5. Event Reactions & Integration
    // -------------------------------------------------------------------------
    describe("Event Reactions & Integration", () => {
        test("refreshes column order state on column-order-changed event", () => {
            const key = "column_order,stock.picking,5";
            mockLocalStorage({ [key]: JSON.stringify(["partner_id", "name"]) });

            const controller = Object.create(ListController.prototype);
            controller._buildColumnOrderKey = () => key;
            controller.columnOrderState = { hasCustomOrder: false };
            let syncCalled = false;
            controller._syncResetButton = () => {
                syncCalled = true;
            };

            const handler = () => controller._refreshColumnOrderState();
            window.addEventListener("column-order-changed", handler);
            after(() => window.removeEventListener("column-order-changed", handler));

            window.dispatchEvent(new CustomEvent("column-order-changed"));
            expect(controller.columnOrderState.hasCustomOrder).toBe(true);
            expect(syncCalled).toBe(true);
        });
    });

    // -------------------------------------------------------------------------
    // 6. Contract Consistency with ListRenderer
    // -------------------------------------------------------------------------
    describe("Contract Consistency with ListRenderer", () => {
        test("both ListRenderer and ListController generate matching localStorage keys", () => {
            const resModel = "account.move";
            const viewId = 999;

            const renderer = Object.create(ListRenderer.prototype);
            renderer.props = { list: { resModel }, archInfo: { viewId } };

            const controller = Object.create(ListController.prototype);
            controller.model = { root: { resModel } };
            controller.props = { archInfo: { viewId } };

            const rendererKey = renderer._buildStorageKey();
            const controllerKey = controller._buildColumnOrderKey();

            expect(rendererKey).toBe(controllerKey);
            expect(rendererKey).toBe(`column_order,${resModel},${viewId}`);
        });
    });
});
