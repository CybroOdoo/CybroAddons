odoo.define('salesperson_pos_order_line.Orderline', function(require) {
    'use strict';
    var models = require('point_of_sale.models');
    var _super_orderline = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        /**
         * Initializes the order line object.
         *
         * @param {Object} attr - The order line attributes.
         * @param {Object} options - The options.
         */
        initialize: function(attr, options) {
            _super_orderline.initialize.call(this, attr, options);
            if (options.json) {
                this.salesperson = this.salesperson;
            }
        },
        /**
         * Initializes the order line object from a JSON object.
         *
         * @param {Object} json - The JSON object.
         */
        init_from_JSON: function(json) {
            _super_orderline.init_from_JSON.apply(this, arguments);
            this.salesperson = json.salesperson;
        },
        /**
         * Exports the order line as a JSON object.
         *
         * @return {Object} - The JSON object.
         */
        export_as_JSON: function() {
            var json = _super_orderline.export_as_JSON.apply(this, arguments);
            json.sales_persons = this.salesperson;
            return json
        },
        /**
         * Sets the salesperson for the order line.
         *
         * @param {Object} sp - The salesperson object.
         */
        set_salesperson: function(sp) {
            this.salesperson = sp[0]
            this.trigger('change', this);
        }
    });
});
