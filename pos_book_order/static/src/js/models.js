/** @odoo-module **/
/*
 * This file is used to add some fields to order class for some reference.
 */

import { Order } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";

patch(Order.prototype, {
    /**
     * Override the setup method to initialize custom signature properties.
     * @param {Object} options - Options passed to the setup method.
     */
    setup(options) {
        super.setup(...arguments);
         if (options.json) {
        this.booking_ref_id= options.json.booking_ref_id || false;
            this.is_booked = options.json.is_booked || false;
            this.booked_data = options.json.booked_data || undefined;
     }
    },
    /**
     * Initialize the order object from a JSON representation.
     * @param {Object} json - JSON data representing the order.
     */
    init_from_JSON(json) {
        super.init_from_JSON(...arguments);
            // this function is overrided for assigning json value to this
        super.init_from_JSON(...arguments);
        this.booking_ref_id= json.booking_ref_id;
        this.is_booked = json.is_booked;
        this.booked_data = json.booked_data
    },
    /**
     * Export the order object as a JSON representation.
     * @returns {Object} JSON data representing the order.
     */
    export_as_JSON() {
        //  this function is overrided for assign this to json for new field
        const json = super.export_as_JSON(...arguments);
        json.booking_ref_id=this.booking_ref_id
        json.booked_data = this.booked_data;
        json.is_booked = this.is_booked;
        return json;
    },
});
