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
        initialize: function(attr, options) {
            _super_orderline.initialize.call(this,attr,options);
            this.uom_id = this.product.get_unit();
        },
        export_as_JSON: function() {
            var result = _super_orderline.export_as_JSON.call(this);
            result.uom_id = this.uom_id;
            return result;
        },
        get_custom_unit: function(){
            return this.uom_id;
        },
        export_for_printing: function() {
            var line = _super_orderline.export_for_printing.apply(this,arguments);
            line.unit_name = this.get_custom_unit().name;
            return line;
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