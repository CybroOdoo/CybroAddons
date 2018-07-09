odoo.define('product_multi_uom_pos.multi_uom',function(require) {
"use strict";

var gui = require('point_of_sale.gui');
var PosBaseWidget = require('point_of_sale.BaseWidget');
var core = require('web.core');
var models = require('point_of_sale.models');
var OrderlineSuper = models.Orderline;
var pos_screens = require('point_of_sale.screens');

var MultiUomWidget = PosBaseWidget.extend({
    template: 'MultiUomWidget',
    init: function(parent, args) {
        this._super(parent, args);
        this.options = {};
        this.uom_list = [];
    },
    events: {
        'click .button.cancel':  'click_cancel',
        'click .button.confirm': 'click_confirm',
    },
    /*function returns all the uom s in the specified category*/
    get_units_by_category: function(uom_list, categ_id){
        var uom_by_categ = []
        for (var uom in uom_list){
            if(uom_list[uom].category_id[0] == categ_id[0]){
                uom_by_categ.push(uom_list[uom]);
            }
        }
        return uom_by_categ;
    },
    /*Find the base price(price of the product for reference unit)*/
    find_reference_unit_price: function(product, product_uom){
        if(product_uom.uom_type == 'reference'){
            return product.price;
        }
        else if(product_uom.uom_type == 'smaller'){
           return (product.price * product_uom.factor);
        }
        else if(product_uom.uom_type == 'bigger'){
           return (product.price / product_uom.factor_inv);
        }
    },
    /*finds the latest price for the product based on the new uom selected*/
    get_latest_price: function(uom, product){
        var uom_by_category = this.get_units_by_category(this.pos.units_by_id, uom.category_id);
        var product_uom = this.pos.units_by_id[product.uom_id[0]];
        var ref_price = this.find_reference_unit_price(product, product_uom);
        var ref_unit = null;
        for (var i in uom_by_category){
            if(uom_by_category[i].uom_type == 'reference'){
                ref_unit = uom_by_category[i];
                break;
            }
        }
        if(ref_unit){
            if(uom.uom_type == 'bigger'){
                return (ref_price * uom.factor_inv);
            }
            else if(uom.uom_type == 'smaller'){
                return (ref_price / uom.factor);
            }
            else if(uom.uom_type == 'reference'){
                return ref_price;
            }
        }
        return product.price;
    },
    /*Rendering the wizard*/
    show: function(options){
        options = options || {};
        var current_uom = this.pos.units_by_id[options.uom_list[0]];
        var uom_list = this.pos.units_by_id;
        var uom_by_category = this.get_units_by_category(uom_list, current_uom.category_id);
        this.uom_list = uom_by_category;
        this.current_uom = options.uom_list[0];
        this.renderElement();
    },
    close: function(){
        if (this.pos.barcode_reader) {
            this.pos.barcode_reader.restore_callbacks();
        }
    },
    click_confirm: function(){
        var self = this;
        var uom = parseInt(this.$('.uom').val());
        var order = self.pos.get_order();
        var orderline = order.get_selected_orderline();
        var selected_uom = this.pos.units_by_id[uom];
        orderline.uom_id = [];
        orderline.uom_id[0] = uom;
        orderline.uom_id[1] = selected_uom.display_name;

        /*Updating the orderlines*/
        order.remove_orderline(orderline);
        order.add_orderline(orderline);
        var latest_price = this.get_latest_price(selected_uom, orderline.product);
        order.get_selected_orderline().set_unit_price(latest_price);
        this.gui.close_popup();
        return;

    },
    click_cancel: function(){
        this.gui.close_popup();
    },
});
gui.define_popup({name:'multi_uom_screen', widget: MultiUomWidget});

models.Orderline = models.Orderline.extend({
    /*Adding uom_id to orderline*/
    initialize: function(attr,options){
        OrderlineSuper.prototype.initialize.call(this, attr, options);
        this.uom_id = this ? this.product.uom_id: [];
    },
    export_as_JSON: function() {
        var result = OrderlineSuper.prototype.export_as_JSON.call(this);
        result.uom_id = this.uom_id;
        return result;
    },
    /*this function now will return the uom_id of the orderline ,
    instead of the default uom_id of the product*/
    get_unit: function(){
        var res = OrderlineSuper.prototype.get_unit.call(this);

        var unit_id = this.uom_id;
        if(!unit_id){
            return res;
        }
        unit_id = unit_id[0];
        if(!this.pos){
            return undefined;
        }
        return this.pos.units_by_id[unit_id];
    }
});

pos_screens.ActionpadWidget.include({
    /*opening the wizard on button click*/
    renderElement: function() {
        this._super();
        var self = this;
        this.$('.multi-uom-span').click(function(){
            var orderline = self.pos.get_order().get_selected_orderline();
            var options = {
                'uom_list': orderline.product.uom_id
            };
            self.gui.show_popup('multi_uom_screen', options);
        });
    }
});

});