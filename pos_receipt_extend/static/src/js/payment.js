/** @odoo-module */

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { usePos } from "@point_of_sale/app/store/pos_hook";

patch(PaymentScreen.prototype, {
      setup() {
        super.setup();
        this.orm = useService("orm");
        this.pos = usePos();
      },
    async validateOrder(isForceValidate) {
//    extending  the validate order to add the below fields
        let receipt_order = await super.validateOrder(arguments);
        var receipt_number = this.pos.selectedOrder.name;
        var orders = this.env.services.pos.selectedOrder;

        const data = this.env.services.pos.session_orders;
        var length = data.length-1;
        var order = data[length];
        var mobile = order.customer_mobile;
        var phone = order.customer_phone;
        var email = order.customer_email;
        var vat = order.customer_vat;
        var address = order.customer_address;
        var name = order.customer_name;
        var customer_details = order.customer_details;
        var self = this;

        this.pos.customer_details = order.customer_details;
        this.pos.mobile = order.customer_mobile;
        this.pos.phone = order.customer_phone;
        this.pos.email = order.customer_email;
        this.pos.vat = order.customer_vat;
        this.pos.address = order.customer_address;
        this.pos.name = order.customer_name;
        return receipt_order;
    },
});
