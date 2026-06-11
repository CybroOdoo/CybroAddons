/** @odoo-module **/

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { SignaturePopup } from "./signature_popup";

patch(PaymentScreen, {
    components: {
        ...PaymentScreen.components,
        SignaturePopup,
    },
});


patch(PaymentScreen.prototype, {
    setup() {
        super.setup();
        this.popup = useService("popup");
    },

    async captureSignature() {
        const { confirmed, payload } = await this.popup.add(SignaturePopup);
        if (confirmed) {
            this.currentOrder.set_customer_signature(payload);
        }
    },
});
