/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { ActionpadWidget } from "@point_of_sale/app/screens/product_screen/action_pad/action_pad";
import { useService } from "@web/core/utils/hooks";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";
import { TicketScreen } from "@point_of_sale/app/screens/ticket_screen/ticket_screen";
import { changesToOrder } from "@point_of_sale/app/models/utils/order_change";

/**
 * @props partner
 */
patch(ActionpadWidget.prototype, {
    setup() {
        super.setup();
        this.orm = useService("orm");
        console.log("ActionpadWidget")
    },

    get swapButton() {
        return (
            this.pos.config.module_pos_restaurant && this.pos.mainScreen.component !== TicketScreen
        );
    },

    get currentOrder() {
        return this.pos.get_order();
    },

    get swapButtonClasses() {
        return {
            "highlight btn-primary justify-content-between": this.displayCategoryCount.length,
            "btn-light pe-none disabled justify-content-center": !this.displayCategoryCount.length,
            altlight: !this.hasChangesToPrint && this.currentOrder?.hasSkippedChanges(),
        };
    },

    async submitOrder() {
        var self = this;
        if (!this.uiState.clicked) {
            this.uiState.clicked = true;
            try {
                await self.orm.call("pos.order", "check_order_status", ["", this.pos.get_order().pos_reference]).then(function(result){
                    if (result == false){
                        self.kitchen_order_status = false
                        self.env.services.dialog.add(AlertDialog, {
                            title: _t("Order is Completed"),
                            body: _t("This Order is Completed. Please create a new Order"),
                        });
                    }
                    else{
                         self.kitchen_order_status = true
                    }
                });
                if (self.kitchen_order_status){
                    // Capture, BEFORE sending, both the new quantities and the
                    // cancellations relative to the previous kitchen send. The
                    // send resets the native tracker, so this is the only moment
                    // the diff is available.
                    const order = this.currentOrder;
                    const orderUuid = order.uuid;
                    const configId = order.config_id.id;
                    const orderRef = order.pos_reference || order.name || "";
                    const tableName = order.table_id ? order.table_id.name : "";
                    const { newQtyByUuid, cancelled, currentQtyByUuid } = this._collectKitchenChanges(order);
                    await this.pos.sendOrderInPreparationUpdateLastChange(order);
                    await this.processOrderForKitchen();
                    if (orderUuid && (Object.keys(newQtyByUuid).length || Object.keys(currentQtyByUuid).length)) {
                        await self.orm.call("pos.order", "apply_kitchen_new_quantities", [orderUuid, newQtyByUuid, currentQtyByUuid]);
                    }
                    if (cancelled.length) {
                        await self.orm.call("kitchen.order.cancellation", "record_cancellations", [configId, orderRef, tableName, cancelled]);
                    }
                    this.env.bus.trigger('pos-kitchen-screen-update');
                }
            } finally {
                this.uiState.clicked = false;
            }
        }
    },

    _collectKitchenChanges(order) {
        // Single call to Odoo's native preparation-change computation (the one
        // that feeds the kitchen printer): it returns both the newly added
        // quantities and the cancelled/reduced ones since the previous send.
        const newQtyByUuid = {};
        const cancelled = [];
        const changedUuids = new Set();
        try {
            const change = changesToOrder(order, false, new Set(), false);
            for (const line of change.new || []) {
                if (line.uuid && line.quantity > 0) {
                    newQtyByUuid[line.uuid] = (newQtyByUuid[line.uuid] || 0) + line.quantity;
                    changedUuids.add(line.uuid);
                }
            }
            const cancelledByProduct = {};
            for (const line of change.cancelled || []) {
                if (line.quantity > 0) {
                    // Group by product so several cancelled lines of the same
                    // product show a single "N x Product" alert instead of one
                    // alert per line.
                    const key = line.product_id || line.name || line.basic_name || line.display_name;
                    if (!cancelledByProduct[key]) {
                        cancelledByProduct[key] = {
                            product_id: line.product_id,
                            name: line.name || line.basic_name || line.display_name,
                            quantity: 0,
                        };
                    }
                    cancelledByProduct[key].quantity += line.quantity;
                    if (line.uuid) {
                        changedUuids.add(line.uuid);
                    }
                }
            }
            cancelled.push(...Object.values(cancelledByProduct));
        } catch (e) {
            console.info("Could not compute kitchen changes", e);
        }
        // Authoritative current quantity per changed line (0 if removed), so the
        // kitchen screen reflects reductions/cancellations regardless of how the
        // POS persists already-sent order lines.
        const presentQty = {};
        for (const l of order.get_orderlines()) {
            presentQty[l.uuid] = l.get_quantity();
        }
        const currentQtyByUuid = {};
        for (const uuid of changedUuids) {
            currentQtyByUuid[uuid] = presentQty[uuid] || 0;
        }
        return { newQtyByUuid, cancelled, currentQtyByUuid };
    },

    async processOrderForKitchen() {
        var self = this;
        const orderData = {
            'pos_reference': this.pos.get_order().pos_reference,
            'config_id': this.pos.get_order().config_id.id,
            'table_id': this.pos.get_order().table_id.id,
            'session_id': this.pos.get_order().session_id.id
        };
        await this.pos.syncAllOrders();
        await self.orm.call("pos.order", "process_order_for_kitchen", [orderData]);
    },

    hasQuantity(order) {
        if (!order) {
            return false;
        } else {
            return (
                order.lines.reduce((totalQty, line) => totalQty + line.get_quantity(), 0) > 0
            );
        }
    },

    get highlightPay() {
        return (
            this.currentOrder?.lines?.length &&
            !this.hasChangesToPrint &&
            this.hasQuantity(this.currentOrder)
        );
    },

    get hasChangesToPrint() {
        let hasChange = this.pos.getOrderChanges();
        hasChange =
            hasChange.generalNote == ""
                ? true // for the case when removed all general note
                : hasChange.count || hasChange.generalNote || hasChange.modeUpdate;
        return hasChange;
    },

    get categoryCount() {
        const orderChanges = this.getOrderChanges();
        const linesChanges = orderChanges.orderlines;
        const categories = Object.values(linesChanges).reduce((acc, curr) => {
            const categories =
                this.models["product.product"].get(curr.product_id)?.pos_categ_ids || [];
            for (const category of categories.slice(0, 1)) {
                if (!acc[category.id]) {
                    acc[category.id] = {
                        count: curr.quantity,
                        name: category.name,
                    };
                } else {
                    acc[category.id].count += curr.quantity;
                }
            }
            return acc;
        }, {});
        return [
            ...Object.values(categories),
            ...("generalNote" in orderChanges ? [{ count: 1, name: _t("General Note") }] : []),
        ];
    },

    get displayCategoryCount() {
        return this.pos.categoryCount.slice(0, 4);
    },

    get isCategoryCountOverflow() {
        if (this.pos.categoryCount.length > 4) {
            return true;
        }
        return false;
    },
});

