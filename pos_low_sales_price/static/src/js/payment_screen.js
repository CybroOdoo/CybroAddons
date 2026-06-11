/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";
//Checks whether the sale price greater than cost price each orderlines
patch(PaymentScreen.prototype, {
    async validateOrder(isForceValidate) {
        var self = this
        var product_list = [];
        var orderlines = this.pos.selectedOrder.get_orderlines();
        // Checking condition for each orderlines
        for (const line of orderlines) {
            if (line.product_id.lst_price < line.product_id.standard_price || line.price_unit < line.product_id.standard_price) {
                product_list.push("'" + line.product_id.display_name + "'");
            }
        }
        if (product_list.length > 0) {
            var content = '';
            if (product_list.length === 1) {
                content = 'The Sales Price of ' + product_list.join(' ') +
                    ' is less than the Cost Price. Do you want to continue validation?';
            } else {
                var lastIndex = product_list.length - 1;
                product_list[lastIndex] = "and " + product_list[lastIndex];
                content = 'The Sales Prices of ' + product_list.join(', ') +
                    ' are less than the Cost Price. Do you want to continue validation?';
            }
            this.dialog.add(ConfirmationDialog, {
                title: _t("Alert"),
                body: _t(content),
                confirm: () => {
                    super.validateOrder(isForceValidate);
                },
                cancel: () => {},
            });
        } else {
            super.validateOrder(isForceValidate);
        }
    }
});
export default PaymentScreen;