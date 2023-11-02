odoo.define('carry_bag_pos.models', function (require) {
"use strict";
var {PosGlobalState} = require('point_of_sale.models');
const Registries = require('point_of_sale.Registries');
const GlobalState = (PosGlobalState) => class GlobalState extends PosGlobalState {
      /**
         *Override PosGlobalState to load fields in pos session
      */
     async _processData(loadedData){
        // Load res config settings model
        await super._processData(...arguments);
        this.res_config_settings = loadedData['res.config.settings'];
    }
}
Registries.Model.extend(PosGlobalState,GlobalState)
});
