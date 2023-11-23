odoo.define('salesperson_pos_order_line.Orderline', function(require) {
    'use strict';
    const { Orderline } = require('point_of_sale.models');
    const Registries = require('point_of_sale.Registries');
    /**
     * A class that extends the default `Orderline` class to include a `salesperson` property
     * that can be added to an order line.
     */
    const SalesPersonOrderline = (Orderline) => class SalesPersonOrderline extends Orderline {
        /**
         * Initializes a new instance of the `SalesPersonOrderline` class.
         * 
         * @param {Object} obj - The order line object.
         * @param {Object} options - The options for the order line.
         */
        constructor(obj, options) {
            super(obj, options)
            if (options.json) {
                this.salesperson = options.json.salesperson;
            }
        }
        /**
         * Initializes the `SalesPersonOrderline` instance from JSON.
         * 
         * @param {Object} json - The JSON object to initialize from.
         */
        init_from_JSON(json) {
            super.init_from_JSON(json)
            this.salesperson = json.salesperson;
        }
        /**
         * Exports the `SalesPersonOrderline` instance as a JSON object.
         * 
         * @returns {Object} - The JSON object that represents the order line.
         */
        export_as_JSON() {
            if (this.salesperson) {
                var user_id = this.salesperson[0]
            } else {
                var user_id = ''
            }
            return _.extend(super.export_as_JSON(...arguments), {
                user_id: user_id
            })
        }
    }
    Registries.Model.extend(Orderline, SalesPersonOrderline);
});
