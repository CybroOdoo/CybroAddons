/** @odoo-module **/
//    Pos session
    var { PosGlobalState, Order } = require('point_of_sale.models');
    const Registries = require('point_of_sale.Registries');
    const NewPosGlobalState = (PosGlobalState) => class NewPosGlobalState extends PosGlobalState {
       async _processData(loadedData) {
       // Load field that in pos.order.question into pos.
         await super._processData(...arguments);
         this.order_questions = loadedData['pos.order.question'];
         }
    }
Registries.Model.extend(PosGlobalState, NewPosGlobalState);
