/** @odoo-module **/

import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { patch } from "@web/core/utils/patch";

/**
 * Patch for PosOrder to include partial payment logic.
 */
patch(PosOrder.prototype, {
    /**
     * Initialize partial payment flags during setup.
     */
    setup() {
        super.setup(...arguments);
        this.is_partial_payment = this.is_partial_payment || false;
    },

    /**
     * Logic for partial payment suggestions.
     * @param {Boolean} suggestion
     */
    set_order_suggestion(suggestion) {
        this.is_partial_payment = suggestion;
    },

    /**
     * Include 'is_partial_payment' in serialized data sent to the server.
     * @param {Object} options
     * @returns {Object}
     */
    serialize(options = {}) {
        const res = super.serialize(...arguments);
        if (options.orm) {
            res.is_partial_payment = this.is_partial_payment;
        }
        return res;
    },
});
