/** @odoo-module **/

    var { PosGlobalState } = require('point_of_sale.models');
    const Registries = require('point_of_sale.Registries');

    const NewPosGlobalState = (PosGlobalState) => class NewPosGlobalState extends PosGlobalState {
       async _processData(loadedData) {
       // load field that in res.config.settings into pos.
         await super._processData(...arguments);
         this.res_button = loadedData['res.config.settings'];
         }
    }
Registries.Model.extend(PosGlobalState, NewPosGlobalState);
