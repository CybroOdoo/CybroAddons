odoo.define('pos_alternative_products.models', function(require) {
    "use strict";
    var models = require('point_of_sale.models');
    /**
     * Loading the required model and fields
     */
     models.load_fields('product.product', 'alternative_product_ids');
    models.load_models({
        model: 'product.template',
        fields: ['display_name', 'default_code'],
        loaded: function(self, product_template) {
            self.product_template = product_template;
        }
    });
});
