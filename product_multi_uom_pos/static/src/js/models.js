odoo.define('product_multi_uom_pos.models',function(require) {
"use strict";

var core = require('web.core');
var models = require('point_of_sale.models');
var OrderlineSuper = models.Orderline;
var field_utils = require('web.field_utils');
var QWeb = core.qweb;
var _t = core._t;
var utils = require('web.utils');
var round_pr = utils.round_precision;
var _super_orderline = models.Orderline.prototype;



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



models.Order = models.Order.extend({

    updatePricelist: function(newClient) {
        let newClientPricelist, newClientFiscalPosition;
        const defaultFiscalPosition = this.pos.fiscal_positions.find(
            (position) => position.id === this.pos.config.default_fiscal_position_id[0]
        );
        if (newClient) {
            newClientFiscalPosition = newClient.property_account_position_id
                ? this.pos.fiscal_positions.find(
                      (position) => position.id === newClient.property_account_position_id[0]
                  )
                : defaultFiscalPosition;
            newClientPricelist =
                this.pos.pricelists.find(
                    (pricelist) => pricelist.id === newClient.property_product_pricelist[0]
                ) || this.pos.default_pricelist;
        } else {
            newClientFiscalPosition = defaultFiscalPosition;
            newClientPricelist = this.pos.default_pricelist;
        }


        if (this.selected_orderline.uom_id != this.selected_orderline.product.uom_id){
            this.fiscal_position = newClientFiscalPosition;

        }else{
            this.fiscal_position = newClientFiscalPosition;
            this.set_pricelist(newClientPricelist);

        }


    }



});


});