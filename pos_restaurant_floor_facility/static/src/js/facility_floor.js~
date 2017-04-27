odoo.define('pos_restaurant_floor_facility.floor_facility_rate_addition', function (require) {
'use strict';
alert("aaaaaaaa");
var models = require('point_of_sale.models');
var screens = require('point_of_sale.screens');
var restaurant = require('pos_restaurant.floors');

models.load_fields("restaurant.floor",['facility_service_percentage']);

screens.ProductScreenWidget.include({
    click_product: function(product) {
               if(product.to_weight && this.pos.config.iface_electronic_scale){
                   this.gui.show_screen('scale',{product: product});
               }else{
                   this.pos.get_order().add_product(product,{ price: product.price +
                   (product.price * this.pos.table.floor.facility_service_percentage)/100});
               }
        }
});
});