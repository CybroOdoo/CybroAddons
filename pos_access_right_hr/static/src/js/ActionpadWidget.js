/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { ActionpadWidget } from "@point_of_sale/app/screens/product_screen/action_pad/action_pad";

//Patching ActionpadWidget to disable customer and payment
patch(ActionpadWidget.prototype, {
    setup() {
        super.setup();
    },
    disable_customer() {
        if (this.pos.cashier?.disable_customer) {
            return true;
        } else {
            return false;
        }
    },
    disable_payment() {
        console.log(this.pos.cashier?.disable_customer)
        if (this.pos.cashier?.disable_payment) {
            return true;
        } else {
            return false;
        }
    }
});
