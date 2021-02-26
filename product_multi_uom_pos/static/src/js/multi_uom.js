odoo.define('product_multi_uom_pos.multi_uom',function(require) {
"use strict";

console.log("multi_uom_main")

var gui = require('point_of_sale.gui');
var core = require('web.core');
var models = require('point_of_sale.models');
var pos_screens = require('point_of_sale.screens');
var field_utils = require('web.field_utils');
var rpc = require('web.rpc');
var QWeb = core.qweb;
var _t = core._t;
var utils = require('web.utils');
var round_pr = utils.round_precision;



//pos_screens.OrderWidget.include({
// set_value: function(val) {
//                this._super();
//    	var order = this.pos.get_order();
//    	var orderline = order.get_selected_orderline();
//    	var uom = orderline.uom_id[0];
//    	var lst_uom = this.pos.units_by_id[uom];
//    	if (order.get_selected_orderline()) {
//
//
//            var orderline = order.get_selected_orderline();
//    	    var latestprice = orderline.lst_price;
//            var current_pricelist = this.pos.default_pricelist;
//    	    orderline.set_unit_price(latestprice);
//            var mode = this.numpad_state.get('mode');
//            if( mode === 'quantity'){
//            var selected_orderline = order.get_selected_orderline();
//                selected_orderline.set_unit_price(latestprice);
//                order.get_selected_orderline().set_quantity(val);
//            }else if( mode === 'discount'){
//                order.get_selected_orderline().set_discount(val);
//            }else if( mode === 'price'){
//                var selected_orderline = order.get_selected_orderline();
//                selected_orderline.price_manually_set = true;
//                selected_orderline.set_unit_price(val);
//            }
//            if (this.pos.config.iface_customer_facing_display) {
//                this.pos.send_current_order_to_customer_facing_display();
//            }
//    	}
//    },
//    });
//
//
//
//});


//    updatePricelist: function(newClient) {
//        let newClientPricelist, newClientFiscalPosition;
//        const defaultFiscalPosition = this.pos.fiscal_positions.find(
//            (position) => position.id === this.pos.config.default_fiscal_position_id[0]
//        );
//        if (newClient) {
//            newClientFiscalPosition = newClient.property_account_position_id
//                ? this.pos.fiscal_positions.find(
//                      (position) => position.id === newClient.property_account_position_id[0]
//                  )
//                : defaultFiscalPosition;
//            newClientPricelist =
//                this.pos.pricelists.find(
//                    (pricelist) => pricelist.id === newClient.property_product_pricelist[0]
//                ) || this.pos.default_pricelist;
//        } else {
//            newClientFiscalPosition = defaultFiscalPosition;
//            newClientPricelist = this.pos.default_pricelist;
//        }
//
//
//        if (this.selected_orderline.uom_id != this.selected_orderline.product.uom_id){
//            this.fiscal_position = newClientFiscalPosition;
//
//        }else{
//            this.fiscal_position = newClientFiscalPosition;
//            this.set_pricelist(newClientPricelist);
//
//        }
//
//
//    }