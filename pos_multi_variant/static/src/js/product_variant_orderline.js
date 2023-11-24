odoo.define('pos_order_question.Orderline', function(require) {
    'use strict';
      /* This JavaScript code defines the PosMultiVariantOrderline class
     * extending the Orderline class from the point_of_sale.models module.
     * It adds additional functionality related to product variants.
     */
    var {
        Orderline,
    } = require('point_of_sale.models');
    var utils = require('web.utils');
    const Registries = require('point_of_sale.Registries');

    const PosMultiVariantOrderline = (Orderline) => class PosMultiVariantOrderline extends Orderline {

        constructor(obj, options) {
            super(...arguments);
            this.product_variants = this.product_variants || [];
        }
        export_as_JSON() {
            const json = super.export_as_JSON(...arguments);
            json.product_variants = this.product_variants || [];
            return json;
        }
        export_for_printing() {
            var line = super.export_for_printing(...arguments);
            line.product_variants = this.product_variants;
            return line;
        }
    }
    Registries.Model.extend(Orderline, PosMultiVariantOrderline);
});



