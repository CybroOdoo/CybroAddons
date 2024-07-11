/** @odoo-module */

import { Order } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";

// Loading the field delivery method into POS
patch(Order.prototype, {
    setup(_defaultObj, options) {
        super.setup(...arguments);
       this.delivery_method = this.delivery_method || false
    },

    init_from_JSON(json) {
        super.init_from_JSON(...arguments);
         this.delivery_method = json.delivery_method;
    },

    export_as_JSON() {
        const json = super.export_as_JSON(...arguments);
        json.delivery_method = this.delivery_method;
        return json;
    },
});
