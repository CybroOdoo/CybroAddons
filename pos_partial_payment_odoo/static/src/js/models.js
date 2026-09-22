/** @odoo-module **/

import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { patch } from "@web/core/utils/patch";

/**
 * Patch for PosOrder to support partial payment flag persistence.
 *
 * This patch:
 *  - Initializes a custom `is_partial_payment` flag on the order
 *  - Allows setting the flag dynamically
 *  - Ensures the flag is exported to JSON (for backend sync)
 *  - Restores the flag when loading an order from JSON
 */
patch(PosOrder.prototype, {

    /**
     * Setup lifecycle hook.
     *
     * Initializes the `is_partial_payment` flag when the order
     * object is created. Defaults to `false` if not already set.
     */
    setup() {
        super.setup(...arguments);
        this.is_partial_payment = this.is_partial_payment || false;
    },

    /**
     * Set partial payment suggestion on the order.
     *
     * @param {Boolean} suggestion
     *  Indicates whether the order is marked as a partial payment.
     */
    set_order_suggestion(suggestion) {
        this.is_partial_payment = suggestion;
    },

    /**
     * Export order data to JSON.
     *
     * Adds the `is_partial_payment` flag to the exported JSON
     * so it can be stored in the database and sent to the backend.
     *
     * @returns {Object}
     *  Serialized order data.
     */
    export_as_JSON() {
        const json = super.export_as_JSON(...arguments);
        json.is_partial_payment = this.is_partial_payment;
        return json;
    },

    /**
     * Initialize order from JSON.
     *
     * Restores the `is_partial_payment` flag when an order
     * is reloaded from stored JSON data.
     *
     * @param {Object} json
     *  Serialized order data.
     */
    init_from_JSON(json) {
        super.init_from_JSON(...arguments);
        this.is_partial_payment = json.is_partial_payment || false;
    },
});
