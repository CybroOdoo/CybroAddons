/** @odoo-module **/
//    Extend POS global state
    var { PosGlobalState, Order } = require('point_of_sale.models');
    const Registries = require('point_of_sale.Registries');
    const NewPosGlobalState = (PosGlobalState) => class NewPosGlobalState extends PosGlobalState {
       async _processData(loadedData) {
         await super._processData(...arguments);
         // Load field values of in pos.payment into pos.
         this.user_payment_reference = loadedData['pos.payment'];
         // Load field values of in res.config.settings into pos.
         this.is_allow_payment_ref = loadedData['res.config.settings'];
         }
    }
Registries.Model.extend(PosGlobalState, NewPosGlobalState);
