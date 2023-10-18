odoo.define('product_multi_uom_pos.pos_multi_uom_load', function (require) {
"use strict";
    // Import the required modules
    var {PosGlobalState} = require('point_of_sale.models');
    const Registries = require('point_of_sale.Registries');
    // Extend the PosGlobalState class
    const NewPosGlobalState = (PosGlobalState) => class NewPosGlobalState extends PosGlobalState {
    async _processData(loadedData){
        await super._processData(...arguments);
        // Assign the loaded 'pos.multi.uom' data to the pos_multi_uom property
        this.pos_multi_uom = loadedData['pos.multi.uom'];
        }
    }
    // Extend the PosGlobalState model using the NewPosGlobalState class
    Registries.Model.extend(PosGlobalState,NewPosGlobalState)
 });
