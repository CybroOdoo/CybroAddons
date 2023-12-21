odoo.define('pos_takeaway.receipt', function (require) {
    'use strict';
//  Loading fields from the model
    const models = require('point_of_sale.models');
    models.load_fields('pos.order', 'is_takeaway');
    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
    initialize: function() {
        //@Override
        /** Sets the values of the fields is_take_way and is_restaurant */
        _super_order.initialize.apply(this,arguments);
        this.is_restaurant = this.pos.config.module_pos_restaurant || false;
        this.is_take_way = this.is_take_way || false;
        this.rpc = this.get('rpc');
        this.save_to_db();
    },
    });
});
