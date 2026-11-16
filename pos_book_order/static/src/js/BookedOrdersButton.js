/** @odoo-module **/
import { _t } from "@web/core/l10n/translation";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { patch } from "@web/core/utils/patch";
import { BookOrderPopup } from "./BookOrderPopup";



patch(ControlButtons.prototype, {
    async bookOrder() {
        if (!this.pos.config.enable) {
            return;
        }
        const order = this.currentOrder;
        const order_lines = this.currentOrder?.lines || [];
        const partner = this.partner;
        if (!partner) {
            this.dialog.add(AlertDialog, {
                title: _t("Please Select the Customer"),
                body: _t(
                    "You need to select a customer for using this option"
                ),
            });
        } else if (order_lines.length === 0) {
            this.dialog.add(AlertDialog, {
                title: _t("Order line is empty"),
                body: _t(
                    "Please select at least one product"
                ),
            });
        } else {
            await this.dialog.add(BookOrderPopup, {
                title: _t("Book Order"),
                partner: partner,
                order: order,
            });
        }
    },
    async getBookingOrders() {
        if (!this.pos.config.enable) {
            return;
        }
        const result = await this.pos.data.call("book.order", "all_orders", ["all"]);
        this.pos.navigate("BookedOrdersScreen", { data: result, new_order: false });
    }
});
