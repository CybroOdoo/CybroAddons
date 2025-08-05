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
        var line = []
        var self = this;
        if (!this.clicked) {
            this.clicked = true;
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

                    for (const orders of this.pos.get_order().lines) {
                        let actualQty = orders.qty || orders.quantity || orders.get_quantity() || 1;

                        line.push([0, 0, {
                            'qty': actualQty,
                            'price_unit': orders.price_unit,
                            'price_subtotal': orders.price_subtotal,
                            'price_subtotal_incl': orders.price_subtotal_incl,
                            'discount': orders.discount,
                            'product_id': orders.product_id.id,
                            'tax_ids': [
                                [6, 0, orders.tax_ids.map((tax) => tax.id)]
                            ],
                            'id': orders.id,
                            'pack_lot_ids': [],
                            'full_product_name': orders.product_id.display_name,
                            'price_extra': orders.price_extra,
                            'name': orders.product_id.display_name,
                            'is_cooking': true,
                            'note': orders.note
                        }])
                    }

                    const date = new Date(self.currentOrder.date_order.replace(' ', 'T'));
                    var orders = [{
                        'pos_reference': this.pos.get_order().pos_reference,
                        'session_id': this.pos.get_order().session_id.id,
                        'amount_total': this.pos.get_order().amount_total,
                        'amount_paid': this.pos.get_order().amount_paid,
                        'amount_return': this.pos.get_order().amount_return,
                        'amount_tax': this.pos.get_order().amount_tax,
                        'lines': line,
                        'is_cooking': true,
                        'order_status': 'draft',
                        'company_id': this.pos.company.id,
                        'hour': date.getHours(),
                        'minutes': date.getMinutes(),
                        'table_id': this.pos.get_order().table_id.id,
                        'floor': this.pos.get_order().table_id.floor_id.name,
                        'config_id': this.pos.get_order().config_id.id
                    }]

                    await self.orm.call("pos.order", "create_or_update_kitchen_order", [orders]);
                    this.env.bus.trigger('pos-kitchen-screen-update');
                }
            } finally {
                this.clicked = false;
            }
        }
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
