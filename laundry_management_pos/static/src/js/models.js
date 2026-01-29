odoo.define('laundry_management_pos.modelsorderline', function (require) {
"use strict";

var models = require('point_of_sale.models');
var rpc = require('web.rpc');
var _super_orderline = models.Orderline.prototype;

models.Orderline = models.Orderline.extend({
    initialize: function(attr, options) {
//    It is possible that this orderline is initialized using `init_from_JSON`,
        _super_orderline.initialize.call(this,attr,options);
        this.washingType = this.washingType || options.washingType;
        this.washingType_id = this.washingType_id || 0.0;
        this.washingType_price = this.washingType_id.amount || 0.0;
    },

//    Function to set the service type of the Washing
    set_washingType: function(service) {
        this.washingType = service.value;
        this.washingType_id = service.id;
        this.washingType_price = service.id.amount;
        this.trigger('change',this);
    },
//    Function to get the service type of the Washing
    get_washingType: function(service) {
        return this.washingType;
    },

//    Used to merge the services with Order-line
    can_be_merged_with: function(orderline) {
        if (orderline.get_washingType() !== this.get_washingType()) {
            return false;
        } else {
            return _super_orderline.can_be_merged_with.apply(this,arguments);
        }
    },

// clone the service with order-lines
    clone: function(){
        var orderline = _super_orderline.clone.call(this);
        orderline.washingType = this.washingType;
        orderline.washingType_id = this.washingType_id;
        orderline.washingType_price = this.washingType_price;
        return orderline;
    },
    export_as_JSON: function(){
        var json = _super_orderline.export_as_JSON.call(this);
        json.washingType = this.washingType;
        json.washingType_id = this.washingType_id;
        json.washingType_price = this.washingType_price;
        return json;
    },
    init_from_JSON: function(json){
        _super_orderline.init_from_JSON.apply(this,arguments);
        this.washingType = json.washingType;
        this.washingType_id = json.washingType_id;
        this.washingType_price = json.washingType_price;
    },
});

});
