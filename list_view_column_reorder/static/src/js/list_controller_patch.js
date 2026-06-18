/** @odoo-module **/
import { ListController } from "@web/views/list/list_controller";
import { patch } from "@web/core/utils/patch";
import { browser } from "@web/core/browser/browser";
import { useState, onMounted, onPatched, onWillUnmount, useRef } from "@odoo/owl";

patch(ListController.prototype, {
    setup() {
        super.setup(...arguments);

        this.rootRef = useRef("root");

        // Reactive flag tracked by OWL
        this.columnOrderState = useState({ hasCustomOrder: false });
        this._refreshColumnOrderState();

        // Signal from renderer after a drag-drop save
        this.__columnOrderChangedHandler = () => this._refreshColumnOrderState();
        
        onMounted(() => {
            window.addEventListener("column-order-changed", this.__columnOrderChangedHandler);
            this._syncResetButton();
        });

        // Re-insert button after every OWL re-render (OWL may wipe it
        // because our button is not part of the virtual DOM tree)
        onPatched(() => {
            this._syncResetButton();
        });

        onWillUnmount(() => {
            window.removeEventListener("column-order-changed", this.__columnOrderChangedHandler);
        });
    },

    /**
     * Build the same localStorage key as the renderer patch.
     * Format: column_order,<model>,<viewId>
     */
    _buildColumnOrderKey() {
        const model =
            this.model?.root?.resModel ||
            this.props?.resModel ||
            "unknown";
        const viewId =
            this.props?.archInfo?.viewId ||
            this.env?.config?.viewId ||
            0;
        return `column_order,${model},${viewId}`;
    },

    /**
     * Syncs the reactive flag with localStorage and updates the DOM button.
     */
    _refreshColumnOrderState() {
        const key = this._buildColumnOrderKey();
        this.columnOrderState.hasCustomOrder = !!browser.localStorage.getItem(key);
        // Immediately sync DOM (OWL may not re-render just because localStorage changed)
        this._syncResetButton();
    },

    /**
     * Injects or removes the "Set Default" button next to the "New" button.
     * Called after every mount/patch so OWL re-renders don't permanently lose it.
     */
    _syncResetButton() {
        if (!this.rootRef || !this.rootRef.el) return;

        const existing = this.rootRef.el.querySelector(".o_list_button_reset_columns");

        if (!this.columnOrderState.hasCustomOrder) {
            // Remove if no custom order
            if (existing) existing.remove();
            return;
        }

        // Button should be present — re-create if OWL wiped it
        if (existing) return;

        const newBtn = this.rootRef.el.querySelector(".o_list_button_add");
        if (!newBtn) return;

        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "btn btn-secondary o_list_button_reset_columns ms-1";
        btn.textContent = "Set Default";
        btn.title = "Reset column order to Odoo default";
        btn.addEventListener("click", () => this.resetColumnOrder());
        newBtn.after(btn);
    },

    /**
     * Clears the persisted column order and signals the renderer to reset
     * its in-memory state, causing OWL to re-render in the default order.
     */
    resetColumnOrder() {
        const key = this._buildColumnOrderKey();
        browser.localStorage.removeItem(key);
        this.columnOrderState.hasCustomOrder = false;
        // Remove button immediately without waiting for next patch
        this._syncResetButton();
        // Tell the renderer to wipe its in-memory columnReorderState.order
        window.dispatchEvent(new CustomEvent("column-order-reset"));
    },
});
