/** @odoo-module **/

import { Paymentline } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";

patch(Paymentline.prototype, {
    setup(options) {
        super.setup(...arguments);
        this.user_payment_reference = this.user_payment_reference || "";
    },
    export_as_JSON() {
        const json = super.export_as_JSON(...arguments);
        json.user_payment_reference = this.user_payment_reference;
        return json;
    },
    init_from_JSON(json) {
        super.init_from_JSON(...arguments);
        this.user_payment_reference = json.user_payment_reference;
    },
});
