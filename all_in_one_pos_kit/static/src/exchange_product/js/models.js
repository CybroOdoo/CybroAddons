odoo.define('all_in_one_pos_kit.models', function (require) {
    "use strict";
    var { PosGlobalState, Order} = require('point_of_sale.models');
    const Registries = require('point_of_sale.Registries');
     // Extension of the PosGlobalState class to handle POS session orders.
    const PosSessionOrdersPosGlobalState = (PosGlobalState) => class PosSessionOrdersPosGlobalState extends PosGlobalState {
        /*
        * Process the loaded data and update the POS session orders.
         * @override
         * @param {Object} loadedData - The loaded data containing POS orders and order lines.
         */
        async _processData(loadedData) {
            await super._processData(...arguments);
            this.pos_orders = loadedData['pos.order'];
            this.pos_order_lines = loadedData['pos.order.line'];
        }
    }
    Registries.Model.extend(PosGlobalState, PosSessionOrdersPosGlobalState);// Extend the PosGlobalState class with the PosSessionOrdersPosGlobalState extension
});
