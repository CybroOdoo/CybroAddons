odoo.define('product_exchange_pos_sys.models', function(require) {
    "use strict";
    var models = require('point_of_sale.models');
    /**
     * Loading the required model and fields
     **/
    models.load_models({
        model: 'pos.order',
        fields: ['name', 'date_order', 'pos_reference',
            'partner_id', 'lines', 'is_exchange'
        ],
        loaded: function(self, pos_orders) {
            self.pos_orders = pos_orders;
        }
    }, {
        model: 'pos.order.line',
        fields: ['product_id', 'qty', 'price_subtotal', 'total_cost'],
        loaded: function(self, pos_order_lines) {
            self.pos_order_lines = pos_order_lines;
        }
    });
});
