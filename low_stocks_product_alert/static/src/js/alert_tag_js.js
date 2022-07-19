odoo.define('pos_product_alert_tag.Product', function(require){
    'use strict';

    var models = require('point_of_sale.models');
    var _super_posmodel = models.PosModel.prototype;

    models.PosModel = models.PosModel.extend({

        initialize: function(session, attributes){
            var self = this;
            models.load_fields('product.product', 'alert_tag');
            _super_posmodel.initialize.apply(this, arguments);
        }
    });
});