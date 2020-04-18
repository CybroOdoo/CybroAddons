odoo.define('product_multi_uom_pos.multi_uom',function(require) {
"use strict";

var gui = require('point_of_sale.gui');
var PosBaseWidget = require('point_of_sale.BaseWidget');
var core = require('web.core');
var models = require('point_of_sale.models');
var OrderlineSuper = models.Orderline;
var pos_screens = require('point_of_sale.screens');
var field_utils = require('web.field_utils');

var utils = require('web.utils');

var round_pr = utils.round_precision;

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
            return product.lst_price;
        }
        else if(product_uom.uom_type == 'smaller'){
           return (product.lst_price * product_uom.factor);
        }
        else if(product_uom.uom_type == 'bigger'){
           return (product.lst_price / product_uom.factor_inv);
        }
    },
    /*finds the latest price for the product based on the new uom selected*/
    get_latest_price: function(uom, product){
        var uom_by_category = this.get_units_by_category(this.pos.units_by_id, uom.category_id);
        var product_uom = this.pos.units_by_id[product.uom_id[0]];
        var ref_price = this.find_reference_unit_price(product, product_uom);
        var ref_price = product.lst_price;
        var ref_unit = null;
        for (var i in uom_by_category){
            if(uom_by_category[i].uom_type == 'reference'){
                ref_unit = uom_by_category[i];
                break;
            }
        }
        if(ref_unit){
            if(uom.uom_type == 'bigger'){
                          console.log("bigggg");
                          console.log("ref_price * uom.factor_inv",ref_price * uom.factor_inv);

                return (ref_price * uom.factor_inv);
            }
            else if(uom.uom_type == 'smaller'){
                          console.log("smalll");
                          console.log("small",(ref_price / uom.factor_inv));

                return (ref_price / uom.factor);
            }
            else if(uom.uom_type == 'reference'){
                          console.log("refernce");
                            console.log("ref_price",ref_price);
                return ref_price;
            }
        }
        return product.lst_price;
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
        orderline.lst_price = latest_price;

        this.gui.close_popup();
        return;

    },
    click_cancel: function(){
        this.gui.close_popup();
    },
});
gui.define_popup({name:'multi_uom_screen', widget: MultiUomWidget});



pos_screens.OrderWidget.include({
 set_value: function(val) {
                this._super();
    	var order = this.pos.get_order();
    	var orderline = order.get_selected_orderline();
    	var uom = orderline.uom_id[0];
    	var lst_uom = this.pos.units_by_id[uom];
    	if (order.get_selected_orderline()) {


            var orderline = order.get_selected_orderline();
    	    var latestprice = orderline.lst_price;
            var current_pricelist = this.pos.default_pricelist;
    	    orderline.set_unit_price(latestprice);
            var mode = this.numpad_state.get('mode');
            if( mode === 'quantity'){
            var selected_orderline = order.get_selected_orderline();
                selected_orderline.set_unit_price(latestprice);
                order.get_selected_orderline().set_quantity(val);
            }else if( mode === 'discount'){
                order.get_selected_orderline().set_discount(val);
            }else if( mode === 'price'){
                var selected_orderline = order.get_selected_orderline();
                selected_orderline.price_manually_set = true;
                selected_orderline.set_unit_price(val);
            }
            if (this.pos.config.iface_customer_facing_display) {
                this.pos.send_current_order_to_customer_facing_display();
            }
    	}
    },
    });




models.Orderline = models.Orderline.extend({
    /*Adding uom_id to orderline*/
    initialize: function(attr,options){
        OrderlineSuper.prototype.initialize.call(this, attr, options);
        this.uom_id = this ? this.product.uom_id: [];
    },
    export_as_JSON: function() {
        var result = OrderlineSuper.prototype.export_as_JSON.call(this);
        console.log("result",result);
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
    },

        set_quantity: function(quantity, keep_price) {
         OrderlineSuper.prototype.set_quantity.call(this, quantity, keep_price);
                this.order.assert_editable();
        if(quantity === 'remove'){
            this.order.remove_orderline(this);
            return;
        }else{
            var quant = parseFloat(quantity) || 0;
            var unit = this.get_unit();
            if(unit){
                if (unit.rounding) {
                    var decimals = this.pos.dp['Product Unit of Measure'];
                    var rounding = Math.max(unit.rounding, Math.pow(10, -decimals));
                    this.quantity    = round_pr(quant, rounding);
                    this.quantityStr = field_utils.format.float(this.quantity, {digits: [69, decimals]});
                } else {
                    this.quantity    = round_pr(quant, 1);
                    this.quantityStr = this.quantity.toFixed(0);
                }
            }else{
                this.quantity    = quant;
                this.quantityStr = '' + this.quantity;
            }
        }
        // just like in sale.order changing the quantity will recompute the unit price
        if(! keep_price && ! this.price_manually_set){
            var self = this;
         var order = self.pos.get_order();
        var orderline = order.get_selected_orderline();
        if (orderline){
            var uom = orderline.uom_id[0];
                    var lst_uom = this.pos.units_by_id[uom];
                    var ref_qty = orderline.quantity;
                    var ref_price = orderline.product.lst_price;
                    if (lst_uom.uom_type == 'bigger') {
                            this.set_unit_price(ref_price * lst_uom.factor_inv);
                            this.order.fix_tax_included_price(this);
                    }
                    else if (lst_uom.uom_type == 'smaller') {
                            this.set_unit_price(ref_price / lst_uom.factor);
                            this.order.fix_tax_included_price(this);
                    }
                    else {
                        this.set_unit_price(ref_price);
                        this.order.fix_tax_included_price(this);
                    }

        }
        else{
            this.set_unit_price(this.product.get_price(this.order.pricelist, this.get_quantity()));
            this.order.fix_tax_included_price(this);
        }

        }
        this.trigger('change', this);
         },

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