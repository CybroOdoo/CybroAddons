odoo.define('all_in_one_pos_kit.pos_load_data', function(require) {
    "use strict";
    var { PosGlobalState } = require('point_of_sale.models');
    const Registries = require('point_of_sale.Registries');
    //Custom implementation of PosGlobalState with additional data processing
    const NewPosGlobalState = (PosGlobalState) => class NewPosGlobalState extends PosGlobalState {
        async _processData(loadedData) {
        // Call the super method to perform the default data processing
            await super._processData(...arguments);
            this.res_config_settings = loadedData['res.config.settings'];// Process additional data specific to this module
        }
    }
    Registries.Model.extend(PosGlobalState, NewPosGlobalState);
});
