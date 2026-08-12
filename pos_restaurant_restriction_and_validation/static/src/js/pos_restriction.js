/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { SelectionPopup } from "@point_of_sale/app/utils/input_popups/selection_popup";
import { NumberPopup } from "@point_of_sale/app/utils/input_popups/number_popup";
import { ConfirmPopup } from "@point_of_sale/app/utils/confirm_popup/confirm_popup";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { Navbar } from "@point_of_sale/app/navbar/navbar";

/**
 * Runs the full manager approval workflow using Odoo 17's popup service API.
 *
 * In Odoo 17, popups are opened via `this.popup.add(PopupClass, props)` which
 * returns `{ confirmed, payload }` — NOT the `makeAwaitable`/`ask` API of Odoo 18.
 *
 * @param {object} pos       - The PosStore instance
 * @param {object} popup     - The popup service (useService('popup'))
 * @param {object} orm       - The orm service (useService('orm'))
 * @param {string} action_type
 * @param {number} old_qty
 * @param {number} new_qty
 * @param {number|false} product_id
 * @param {string} order_ref
 * @returns {Promise<boolean>}
 */
async function executeApprovalWorkflow(pos, popup, orm, action_type, old_qty, new_qty, product_id, order_ref) {

    // Step 1: Warning / Confirm popup (Odoo 17 ConfirmPopup API)
    const { confirmed: confirmedApproval } = await popup.add(ConfirmPopup, {
        title: _t("Unauthorised Action"),
        body: _t("You are not authorized to do this action. Please take approval from manager."),
        confirmText: _t("Take Approval"),
        cancelText: _t("Discard"),
    });

    if (!confirmedApproval) {
        return false;
    }

    // Step 2: Fetch managers via ORM service (Odoo 17 uses orm.call, not pos.data.call)
    const managers = await orm.call("pos.config", "get_managers_for_approval", [pos.config.id]);

    const list_of_managers = managers.map(mgr => ({
        id: mgr.id,
        label: mgr.name,
        isSelected: false,
        item: mgr,
    }));

    if (list_of_managers.length === 0) {
        await popup.add(ErrorPopup, {
            title: _t("Error"),
            body: _t("No managers found for approval."),
        });
        return false;
    }

    // Step 3: Select a manager (Odoo 17 SelectionPopup API)
    const { confirmed: managerSelected, payload: selectedManager } = await popup.add(SelectionPopup, {
        title: _t("Select Manager for Approval"),
        list: list_of_managers,
    });

    if (!managerSelected || !selectedManager) {
        return false;
    }

    // Step 4: Enter PIN (Odoo 17 NumberPopup API)
    const { confirmed: pinConfirmed, payload: pin } = await popup.add(NumberPopup, {
        title: _t("Manager PIN"),
        startingValue: "",
        isInputSelected: true,
        formatDisplayedValue: (val) => val.split("").map(() => "*").join(""),
    });

    if (!pinConfirmed || !pin) {
        return false;
    }

    // Step 5: Validate PIN via ORM (Odoo 17)
    const validationResult = await orm.call(
        "pos.config",
        "validate_manager_pin_for_restriction",
        [
            pos.config.id,
            selectedManager.id,
            pin,
            action_type,
            product_id,
            old_qty,
            new_qty,
            order_ref,
        ]
    );

    if (validationResult && validationResult.approved) {
        return true;
    } else {
        await popup.add(ErrorPopup, {
            title: _t("Error"),
            body: _t("Incorrect Password! Approval Failed."),
        });
        return false;
    }
}

// 1. Patch ProductScreen to handle orderline quantity/delete (Numpad)
//    In Odoo 17 there is no OrderSummary component; the numpad logic lives in ProductScreen.
//    ProductScreen has `this.popup` and `this.orm` already set up in setup().
patch(ProductScreen.prototype, {
    async updateSelectedOrderline({ buffer, key }) {
        const order = this.pos.get_order();
        if (!order) return super.updateSelectedOrderline(...arguments);

        const selectedLine = order.get_selected_orderline();
        if (!selectedLine) return super.updateSelectedOrderline(...arguments);

        if (selectedLine && this.pos.numpadMode === "quantity") {
            const val = buffer === null ? "remove" : buffer;
            const currentQty = selectedLine.get_quantity();
            const productName = selectedLine.get_full_product_name();

            // Handle Line Deletion (Backspace)
            if (val === "remove" && this.pos.config.pos_restaurant_restriction && this.pos.config.pos_orderline_delete) {
                const result = await executeApprovalWorkflow(
                    this.pos, this.popup, this.orm,
                    "orderline_delete", currentQty, 0, false, productName
                );
                if (!result) return;
            }
            // Handle Quantity Change
            else if (val !== "remove" && this.pos.config.pos_restaurant_restriction && this.pos.config.pos_orderline_quantity_update) {
                const parsedQty = parseFloat(val);
                if (parsedQty !== currentQty) {
                    const result = await executeApprovalWorkflow(
                        this.pos, this.popup, this.orm,
                        "orderline_quantity_update", currentQty, parsedQty, false, productName
                    );
                    if (!result) return;
                }
            }
        }
        return super.updateSelectedOrderline(...arguments);
    }
});

// 2. Patch PosStore to handle order deletion and session closing.
//    In Odoo 17, order deletion is done via `removeOrder()` (not `deleteOrders()`).
//    `closePos()` exists in both Odoo 17 and 18.
patch(PosStore.prototype, {
    removeOrder(order, removeFromServer = true) {
        // Skip approval for empty or unsynced orders (internal Odoo cleanup)
        if (
            this.config.pos_restaurant_restriction &&
            this.config.pos_order_delete &&
            order.get_orderlines().length > 0
        ) {
            // removeOrder is synchronous in Odoo 17, so we launch the async approval
            // and only proceed if approved. We return early to block the sync call,
            // then re-call after approval.
            if (this._isApprovedOrderRemoval) {
                // Approved — allow the actual removal
                this._isApprovedOrderRemoval = false;
                return super.removeOrder(order, removeFromServer);
            }
            // Trigger async approval flow
            (async () => {
                const popup = this.env.services.popup;
                const orm = this.env.services.orm;
                const result = await executeApprovalWorkflow(
                    this, popup, orm,
                    "delete_order", 0, 0, false, order.name || order.uid
                );
                if (result) {
                    this._isApprovedOrderRemoval = true;
                    this.removeOrder(order, removeFromServer);
                }
            })();
            // Block original synchronous call
            return;
        }
        return super.removeOrder(order, removeFromServer);
    },

    async closePos() {
        if (this.config.pos_restaurant_restriction && this.config.pos_session_close) {
            const popup = this.env.services.popup;
            const orm = this.env.services.orm;
            const currentOrder = this.get_order();
            const result = await executeApprovalWorkflow(
                this, popup, orm,
                "session_close", 0, 0, false,
                currentOrder ? (currentOrder.name || currentOrder.uid) : "Session"
            );
            if (!result) return false;
        }
        return super.closePos(...arguments);
    }
});

// 3. Patch Navbar to handle the explicit "Close Session" menu option
patch(Navbar.prototype, {
    async closeSession() {
        if (this.pos.config.pos_restaurant_restriction && this.pos.config.pos_session_close) {
            const currentOrder = this.pos.get_order();
            const result = await executeApprovalWorkflow(
                this.pos, this.popup, this.env.services.orm,
                "session_close", 0, 0, false,
                currentOrder ? (currentOrder.name || currentOrder.uid) : "Session"
            );
            if (!result) return;
        }
        return super.closeSession(...arguments);
    }
});