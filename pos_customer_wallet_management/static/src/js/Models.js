odoo.define('pos_customer_wallet_management.models', function (require) {
    'use strict';
    // Adding fileds to POS
    const models = require('point_of_sale.models');
    models.load_fields('res.partner', 'wallet_balance');
    models.load_fields('pos.payment.method', 'wallet_journal');
});