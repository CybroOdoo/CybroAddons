odoo.define('pos_receipt_extends.pos_order', function (require) {
"use strict";
const { batched, uuidv4 } = require("point_of_sale.utils");
    var { PosGlobalState, Order} = require('point_of_sale.models');
    const Registries = require('point_of_sale.Registries');
    var rpc = require('web.rpc')
    var Widget = require('web.Widget');

    const PosSessionOrdersPosGlobalState = (PosGlobalState) => class PosSessionOrdersPosGlobalState extends PosGlobalState {
    async _processData(loadedData) {
    await super._processData(...arguments);
    this.session_orders = loadedData['res.config.settings'];
    var json = {
            access_token: this.access_token || '',
        };
      const options = {pos:this};
      this.pos = options.pos;
      this.access_token = uuidv4();
      const address = `${this.pos.base_url}/pos/ticket/validate?access_token=${this.access_token}`
      var receipt_number = this.env.pos.selectedOrder
    $(".orderlines").change(function (){
    const address = `${this.base_url}/pos/ticket/validate?access_token=${this.access_token}`
    });
    } }
Registries.Model.extend(PosGlobalState, PosSessionOrdersPosGlobalState);
});

