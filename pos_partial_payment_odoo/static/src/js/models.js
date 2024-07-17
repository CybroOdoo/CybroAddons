odoo.define('pos_partial_payment_odoo.models', function(require) {
    var models = require('point_of_sale.models');
    models.load_fields('res.partner', ['prevent_partial_payment']);
    models.load_fields('pos.order', ['is_partial_payment'])
});
