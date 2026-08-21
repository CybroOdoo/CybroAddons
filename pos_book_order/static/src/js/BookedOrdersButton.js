/** @odoo-module **/
import { _t } from "@web/core/l10n/translation";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { patch } from "@web/core/utils/patch";
import { BookOrderPopup } from "./BookOrderPopup";



patch(ControlButtons.prototype, {
    async bookOrder() {
        // by clicking the booking order button, it will check whether at least one product and the selected customer or not, after that it will display popup.
        var order = this.currentOrder
        var order_lines = this.currentOrder.lines;
        var partner = this.partner
        if (partner == null) {
            this.dialog.add(AlertDialog, {
                title: _t("Please Select the Customer"),
                body: _t(
                    "You need to select a customer for usig this option"
                ),
            });
        } else if (order_lines.length == 0) {
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

        // fetch all booked order in draft stage to screen
        var self = this
        await this.pos.env.services.orm.call(
            "book.order", "all_orders", [], {}
        ).then(function(result) {
            self.pos.navigate("BookedOrdersScreen",{ data: result, new_order: false });
        })
    }
})
