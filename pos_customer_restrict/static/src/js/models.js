odoo.define('pos_customer_restrict.models', function (require) {
    'use strict';
    const models = require('point_of_sale.models');
//    Loading is_available_in_pos field in POS
    models.load_fields('res.partner', 'is_available_in_pos');
});