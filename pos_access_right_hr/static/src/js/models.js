odoo.define('pos_access_right_hr.models', function(require) {
 'use strict';

    var models = require('point_of_sale.models');
    /**
    To load fields from hr.employee into pos
    **/
    models.load_fields('hr.employee', 'disable_payment');
    models.load_fields('hr.employee', 'disable_customer');
    models.load_fields('hr.employee', 'disable_plus_minus');
    models.load_fields('hr.employee', 'disable_numpad');
    models.load_fields('hr.employee', 'disable_qty');
    models.load_fields('hr.employee', 'disable_discount');
    models.load_fields('hr.employee', 'disable_price');
    models.load_fields('hr.employee', 'disable_remove_button');
});
