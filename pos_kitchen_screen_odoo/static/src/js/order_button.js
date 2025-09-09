/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { ActionpadWidget } from "@point_of_sale/app/screens/product_screen/action_pad/action_pad";
import { useService } from "@web/core/utils/hooks";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";
import { TicketScreen } from "@point_of_sale/app/screens/ticket_screen/ticket_screen";

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
                    await this.pos.sendOrderInPreparationUpdateLastChange(this.currentOrder);
                    await this.processOrderForKitchen();
                    this.env.bus.trigger('pos-kitchen-screen-update');
                }
            } finally {
                this.uiState.clicked = false;
            }
        }
    },

    async processOrderForKitchen() {
        var self = this;
        const orderData = {
            'pos_reference': this.pos.get_order().pos_reference,
            'config_id': this.pos.get_order().config_id.id,
            'table_id': this.pos.get_order().table_id.id,
            'session_id': this.pos.get_order().session_id.id
        };
        this.pos.syncAllOrders()
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

