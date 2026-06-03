/** @odoo-module */

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { usePos } from "@point_of_sale/app/store/pos_hook";

//Patching PaymentScreen
patch(PaymentScreen.prototype, {
      setup() {
        super.setup();
        this.orm = useService("orm");
        this.pos = usePos();
      },
    async validateOrder(isForceValidate) {
//    extending  the validate order to add the below fields
        let receipt_order = await super.validateOrder(arguments);

        console.log('this',this.currentOrder)

        const partner = this.currentOrder.get_partner();
        if (partner) {
            this.pos.mobile = partner.mobile;
            this.pos.phone = partner.phone;
            this.pos.email = partner.email;
            this.pos.vat = partner.vat;
            this.pos.address = partner.contact_address;
            this.pos.name = partner.name;
        }
        return receipt_order;
    },
});
