odoo.define('product_exchange_pos_sys.models', function (require) {
    "use strict";
    var { PosGlobalState, Order} = require('point_of_sale.models');
    const Registries = require('point_of_sale.Registries');

    const PosSessionOrdersPosGlobalState = (PosGlobalState) => class PosSessionOrdersPosGlobalState extends PosGlobalState {
    async _processData(loadedData) {
        await super._processData(...arguments);
        this.pos_orders = loadedData['pos.order'];
        this.pos_order_lines = loadedData['pos.order.line'];

        console.log(this.pos_orders,'this.session_orders')

        }
        }
    Registries.Model.extend(PosGlobalState, PosSessionOrdersPosGlobalState);
});
