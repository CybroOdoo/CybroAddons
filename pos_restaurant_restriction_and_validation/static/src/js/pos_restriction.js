
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { PosStore } from "@point_of_sale/app/services/pos_store";
import { OrderSummary } from "@point_of_sale/app/screens/product_screen/order_summary/order_summary";
import { ClosePosPopup } from "@point_of_sale/app/components/popups/closing_popup/closing_popup";
import { SelectionPopup } from "@point_of_sale/app/components/popups/selection_popup/selection_popup";
import { NumberPopup } from "@point_of_sale/app/components/popups/number_popup/number_popup";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { ask, makeAwaitable } from "@point_of_sale/app/utils/make_awaitable_dialog";

async function executeApprovalWorkflow(pos, dialog, action_type, old_qty, new_qty, product_id, order_ref) {
    // Step 1: Warning Popup
    const confirmedApproval = await ask(dialog, {
        title: _t("Unauthorized Action"),
        body: _t("You are not authorized to do this action. Please take approval from the manager."),
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

    // Step 3: Enter PIN
    const pin = await makeAwaitable(dialog, NumberPopup, {
        title: _t("Manager PIN"),
        subtitle: _t("Enter the PIN"),
        startingValue: "",
        formatDisplayedValue: (val) => val.split("").map(() => "*").join(""),
    });
    if (!pin) {
        return false;
    }
    const cashierUserId = pos.accessRight?.cashierUserId || pos.user?.id || false;
    const cashierName = pos.accessRight?.cashier?.name || pos.user?.name || "";

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
            order_ref,
            cashierUserId,
            cashierName
        ]
    );

    if (validationResult && validationResult.approved) {
        return true;  // Validation Passed
    } else {
        // Validation Failed
        const errorMsg = validationResult?.error || _t("Incorrect PIN! Approval Failed.");
        await ask(dialog, {
            title: _t("Error"),
            body: errorMsg,
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

        // Check main toggle: pos_restaurant_restriction
        if (this.pos.config.pos_restaurant_restriction && selectedLine && this.pos.numpadMode === "quantity") {
            const val = buffer === null ? "remove" : buffer;
            const currentQty = selectedLine.getQuantity ? selectedLine.getQuantity() : selectedLine.qty;
            const product = selectedLine.getProduct ? selectedLine.getProduct() : selectedLine.product_id;
            const productId = product?.id || false;
            const orderRef = order.pos_reference || order.name || "";

            // Check if line was sent to the kitchen (has savedQuantity > 0 or prep_line_ids)
            const isSentToKitchen = (selectedLine.uiState?.savedQuantity > 0) || (selectedLine.prep_line_ids?.length > 0);

            if (isSentToKitchen) {
                const parsedQty = val === "remove" ? 0 : parseFloat(val);

                // Handle Line Deletion (Backspace on empty buffer or setting quantity to 0)
                if ((val === "remove" || parsedQty === 0) && this.pos.config.pos_orderline_delete) {
                    const result = await executeApprovalWorkflow(
                        this.pos, this.dialog, "orderline_delete", currentQty, 0, productId, orderRef
                    );
                    if (!result) return;
                }
                // Handle Quantity Change (when not deleting)
                else if (val !== "remove" && parsedQty !== 0 && parsedQty !== currentQty && this.pos.config.pos_orderline_quantity_update) {
                    const result = await executeApprovalWorkflow(
                        this.pos, this.dialog, "orderline_quantity_update", currentQty, parsedQty, productId, orderRef
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

        // Check main toggle: pos_restaurant_restriction
        if (this.config.pos_restaurant_restriction && this.config.pos_order_delete && orders.length > 0) {
            this._isDeletingWithApproval = true;
            try {
                for (const order of orders) {
                    // Skip approval for empty draft orders that haven't been synchronized or have no lines
                    // (Odoo sometimes deletes these automatically when switching tables)
                    if (order.lines.length === 0 && !order.isSynced) {
                        continue;
                    }

                    // Only restrict if the order has been sent to the kitchen
                    const hasKitchenLines = (order.prepLines?.length > 0) || ((order.prep_order_ids || []).length > 0) || order.lines.some(
                        (line) => (line.uiState?.savedQuantity > 0) || (line.prep_line_ids?.length > 0)
                    );
                    if (!hasKitchenLines) {
                        continue;
                    }

                    const orderRef = order.pos_reference || order.name || "";
                    const result = await executeApprovalWorkflow(
                        this, this.dialog, "delete_order", 0, 0, false, orderRef
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
});

// 3. Patch ClosePosPopup to require manager approval before calling close_session_from_ui
patch(ClosePosPopup.prototype, {
    async closeSession() {
        // Check main toggle: pos_restaurant_restriction
        if (this.pos.config.pos_restaurant_restriction && this.pos.config.pos_session_close) {
            const orderRef = this.pos.session?.name || "";
            const result = await executeApprovalWorkflow(
                this.pos, this.dialog, "session_close", 0, 0, false, orderRef
            );
            if (!result) return false;
        }
        return super.closeSession(...arguments);
    },
});