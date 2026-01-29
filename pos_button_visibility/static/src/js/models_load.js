odoo.define('pos_button_visibility.models_load', function (require) {
    'use strict';

    var models = require('point_of_sale.models');
    /** To load fields into model res user in pos **/
    models.load_fields('res.users', "refund");
    models.load_fields('res.users', "price");
    models.load_fields('res.users', "discount");
    models.load_fields('res.users', "rewards");
});
