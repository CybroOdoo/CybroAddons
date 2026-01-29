
odoo.define('multi_branch_pos.PosMultiBranch', function (require) {
"use strict";

var models = require('point_of_sale.models');

models.load_fields('pos.config', ['branch_name', 'email', 'phone', 'website']);

});