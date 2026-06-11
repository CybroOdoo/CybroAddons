/** @odoo-module **/

import { Order } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";

patch(Order.prototype, {

    set_customer_signature(signature) {
        this.customer_signature = signature;
    },

    export_as_JSON() {
        const json = super.export_as_JSON();
        json.customer_signature = this.customer_signature || false;
        return json;
    },

    init_from_JSON(json) {
        super.init_from_JSON(json);
        this.customer_signature = json.customer_signature || false;
    },

    export_for_printing() {
        const receipt = super.export_for_printing();
        if (this.customer_signature) {
            receipt.customer_signature =
                "data:image/png;base64," + this.customer_signature;
        } else {
            receipt.customer_signature = false;
        }
        return receipt;
    },
});

