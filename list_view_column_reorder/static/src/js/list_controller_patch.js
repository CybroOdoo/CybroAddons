/** @odoo-module **/
import { ListController } from "@web/views/list/list_controller";
import { patch } from "@web/core/utils/patch";
import { browser } from "@web/core/browser/browser";
import { useState, onMounted, onPatched, onWillUnmount, useRef } from "@odoo/owl";

patch(ListController.prototype, {
    setup() {
        super.setup(...arguments);

        this.rootRef = useRef("root");

        this.columnOrderState = useState({ hasCustomOrder: false });
        this._refreshColumnOrderState();

        this.__columnOrderChangedHandler = () => this._refreshColumnOrderState();

        onMounted(() => {
            window.addEventListener("column-order-changed", this.__columnOrderChangedHandler);
            this._syncResetButton();
        });

        onPatched(() => {
            this._syncResetButton();
        });

        onWillUnmount(() => {
            window.removeEventListener("column-order-changed", this.__columnOrderChangedHandler);
        });
    },

    _buildColumnOrderKey() {
        const model =
            this.props?.resModel ||
            this.model?.root?.resModel ||
            "unknown";
        const viewId =
            this.props?.archInfo?.viewId ||
            this.env?.config?.viewId ||
            0;
        const fieldName = this.props?.name || "";
        return `column_order,${model},${viewId}${fieldName ? ',' + fieldName : ''}`;
    },

    _refreshColumnOrderState() {
        const key = this._buildColumnOrderKey();
        let hasCustom = false;
        try {
            for (let i = 0; i < browser.localStorage.length; i++) {
                const k = browser.localStorage.key(i);
                if (k && k.startsWith(key)) {
                    hasCustom = true;
                    break;
                }
            }
        } catch (e) {
            // Fallback
        }
        this.columnOrderState.hasCustomOrder = hasCustom;
        this._syncResetButton();
    },

    _syncResetButton() {
        if (!this.rootRef || !this.rootRef.el) return;

        const existing = this.rootRef.el.querySelector(".o_list_button_reset_columns");

        if (!this.columnOrderState.hasCustomOrder) {
            if (existing) existing.remove();
            return;
        }

        if (existing) return;

        const container =
            this.rootRef.el.querySelector(".o_cp_buttons") ||
            this.rootRef.el.querySelector(".o_control_panel_main_buttons") ||
            this.rootRef.el.querySelector(".o_list_buttons");

        if (!container) return;

        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "btn btn-secondary o_list_button_reset_columns ms-1";
        btn.textContent = "Set Default";
        btn.title = "Reset column order to Odoo default";
        btn.addEventListener("click", () => this.resetColumnOrder());

        const refBtn = container.querySelector(".o_list_button_add, .o_list_button_save");
        if (refBtn) {
            refBtn.after(btn);
        } else {
            container.appendChild(btn);
        }
    },

    resetColumnOrder() {
        const key = this._buildColumnOrderKey();
        try {
            const keysToRemove = [];
            for (let i = 0; i < browser.localStorage.length; i++) {
                const k = browser.localStorage.key(i);
                if (k && k.startsWith(key)) {
                    keysToRemove.push(k);
                }
            }
            keysToRemove.forEach((k) => browser.localStorage.removeItem(k));
        } catch (e) {
            browser.localStorage.removeItem(key);
        }
        this.columnOrderState.hasCustomOrder = false;
        this._syncResetButton();
        window.dispatchEvent(new CustomEvent("column-order-reset"));
    },
});


