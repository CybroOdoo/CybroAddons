odoo.define('service_charges_pos.pos', function(require) {
    "use strict";

    var { PosGlobalState } = require('point_of_sale.models');
    const Registries = require('point_of_sale.Registries');
//model loading to this.res_config_settings
    const NewPosGlobalState = (PosGlobalState) => class NewPosGlobalState extends PosGlobalState {
        async _processData(loadedData) {
            await super._processData(...arguments);
            this.res_config_settings = loadedData['res.config.settings'];
        }
    }
    Registries.Model.extend(PosGlobalState, NewPosGlobalState);

});