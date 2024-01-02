odoo.define('salesperson_pos_order_line.Orderline', function(require) {
    'use strict';
    var models = require('point_of_sale.models');
    var _super_orderline = models.Orderline.prototype;
    // Define the Orderline model and extend its functionality
    models.Orderline = models.Orderline.extend({
        /**
         * Initialize the Orderline model.
         *
         * @param {Object} attr - The Orderline attributes.
         * @param {Object} options - The Orderline options.
         */
        initialize: function(attr, options) {
            _super_orderline.initialize.call(this, attr, options);
            if(options.json) {
                this.salesperson = this.salesperson;
            }
        },
        /**
         * Initialize the Orderline model from a JSON object.
         *
         * @param {Object} json - The JSON object to initialize the model from.
         */
        init_from_JSON: function(json) {
            _super_orderline.init_from_JSON.apply(this, arguments);
            this.salesperson = json.salesperson;
        },

        /**
         * Export the Orderline model as a JSON object.
         *
         * @returns {Object} The Orderline model as a JSON object.
         */
        export_as_JSON: function() {
            var json = _super_orderline.export_as_JSON.apply(this, arguments);
            json.sales_persons = this.salesperson;
            return json;
        },

        /**
         * Set the salesperson for the Orderline.
         *
         * @param {Array} sp - The salesperson to set for the Orderline.
         */
        set_salesperson: function(sp) {
            this.salesperson = sp[0];
            this.trigger('change', this);
        }
    });
});
