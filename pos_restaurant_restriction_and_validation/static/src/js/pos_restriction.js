/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { PosStore } from "@point_of_sale/app/services/pos_store";
import { OrderSummary } from "@point_of_sale/app/screens/product_screen/order_summary/order_summary";
import { SelectionPopup } from "@point_of_sale/app/components/popups/selection_popup/selection_popup";
import { NumberPopup } from "@point_of_sale/app/components/popups/number_popup/number_popup";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { ask, makeAwaitable } from "@point_of_sale/app/utils/make_awaitable_dialog";

async function executeApprovalWorkflow(pos, dialog, action_type, old_qty, new_qty, product_id, order_ref) {

    
    // Step 1: Warning Popup
    const confirmedApproval = await ask(dialog, {
        title: _t("Unauthorised Action"),
        body: _t("You are not authorized to do this action. Please take approval from manager."),
        confirmLabel: _t("Take Approval"),
        cancelLabel: _t("Discard"),
    });

    if (!confirmedApproval) {
        return false;
    }

    // Step 2: Fetch Managers & Show Selection
    const managers = await pos.data.call("pos.config", "get_managers_for_approval", [pos.config.id]);

    const list_of_managers = managers.map(mgr => ({
        id: mgr.id,
        label: mgr.name,
        isSelected: false,
        item: mgr,
    }));

    if (list_of_managers.length === 0) {
        await ask(dialog, {
            title: _t("Error"),
            body: _t("No managers found for approval."),
            confirmLabel: _t("Ok"),
        }, {}, AlertDialog);
        return false;
    }

    const selectedManager = await makeAwaitable(dialog, SelectionPopup, {
        title: _t('Select Manager for Approval'),
        list: list_of_managers,
    });

    if (!selectedManager) {
        return false;
    }

    // Step 3: Enter Password
    const pin = await makeAwaitable(pos.dialog, NumberPopup, {
        title: _t("Manager PIN"),
        subtitle: _t("Enter the pin"),
        startingValue: "",
        formatDisplayedValue: (val) => val.split("").map(() => "*").join(""),
    });
    if (!pin) {
        return false;
    }
    const validationResult = await pos.data.call(
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
            order_ref
        ]
    );

    if (validationResult && validationResult.approved) {
        return true;  // Validation Passed
    } else {
        // Validation Failed
        await ask(dialog, {
            title: _t("Error"),
            body: _t("Incorrect Password! Approval Failed."),
            confirmLabel: _t("Ok"),
        }, {}, AlertDialog);
        return false;
    }
}

// 1. Patch OrderSummary to handle line deletion and quantity updates (Numpad)
patch(OrderSummary.prototype, {
    async updateSelectedOrderline({ buffer, key }) {
        const order = this.pos.getOrder();
        if (!order) return super.updateSelectedOrderline(...arguments);

        const selectedLine = order.getSelectedOrderline();
        if (!selectedLine) return super.updateSelectedOrderline(...arguments);

        if (selectedLine && this.pos.numpadMode === "quantity") {
            const val = buffer === null ? "remove" : buffer;
            const currentQty = selectedLine.getQuantity ? selectedLine.getQuantity() : selectedLine.qty;
            const productName = selectedLine.getProduct ? selectedLine.getProduct().display_name : selectedLine.full_product_name;

            // Handle Line Deletion (Backspace or manual 0)
            if (val === "remove" && this.pos.config.pos_orderline_delete) {
                const result = await executeApprovalWorkflow(
                    this.pos, this.dialog, "orderline_delete", currentQty, 0, false, productName
                );
                if (!result) return;
            } 
            // Handle Quantity Change
            else if (val !== "remove" && this.pos.config.pos_orderline_quantity_update) {
                const parsedQty = parseFloat(val);
                if (parsedQty !== currentQty) {
                    const result = await executeApprovalWorkflow(
                        this.pos, this.dialog, "orderline_quantity_update", currentQty, parsedQty, false, productName
                    );
                    if (!result) return;
                }
            }
        }
        return super.updateSelectedOrderline(...arguments);
    }
});

// 2. Patch PosStore to handle overall order deletion and session closing
patch(PosStore.prototype, {
    async deleteOrders(orders, serverIds = [], ignoreChange = false) {
        // Prevent recursive triggers if already in an approval flow for this instance
        if (this._isDeletingWithApproval) {
            return super.deleteOrders(...arguments);
        }
        
        if (this.config.pos_order_delete && orders.length > 0) {
            this._isDeletingWithApproval = true;
            try {
                for (const order of orders) {
                    // Skip approval for empty draft orders that haven't been synchronized or have no lines
                    // (Odoo sometimes deletes these automatically when switching tables)
                    if (order.lines.length === 0 && !order.isSynced) {
                        continue;
                    }

                    const result = await executeApprovalWorkflow(
                        this, this.dialog, "delete_order", 0, 0, false, order.name || order.pos_reference
                    );
                    if (!result) return false;
                }
                return super.deleteOrders(...arguments);
            } finally {
                this._isDeletingWithApproval = false;
            }
        }
        return super.deleteOrders(...arguments);
    },

    async closePos() {
        if (this.config.pos_session_close) {
            const currentOrder = this.getOrder();
            const result = await executeApprovalWorkflow(
                this, this.dialog, "session_close", 0, 0, false, currentOrder ? (currentOrder.name || currentOrder.pos_reference) : "Session"
            );
            if (!result) return false;
        }
        return super.closePos(...arguments);
    }
});