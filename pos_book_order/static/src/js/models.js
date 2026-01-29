/*
     * This file is used to add some fields to order class for some reference.
*/
odoo.define('pos_book_order.ModelExtend', function (require) {
    "use strict";
var models = require('point_of_sale.models');

    var super_order_model = models.Order.prototype;
    models.Order = models.Order.extend({
        initialize: function (attributes, options) {
        super_order_model.initialize.apply(this, arguments);
        if (options.json) {
            this.is_booked = options.json.is_booked || false;
            this.booked_data = options.json.booked_data || undefined;
        }
        },
        init_from_JSON: function (json){
            // This function is overrided for assigning json value to this
                super_order_model.init_from_JSON.apply(this, arguments);
                this.is_booked = json.is_booked;
                this.booked_data = json.booked_data
        },
        export_as_JSON:function(){
            //  This function is overrided for assign this to json for new field
           const json = super_order_model.export_as_JSON.apply(this, arguments);
            json.booked_data = this.booked_data;
            json.is_booked = this.is_booked;
            return json;
        }

    });
});