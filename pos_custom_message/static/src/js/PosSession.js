/** @odoo-module */
import {
    PosGlobalState
} from 'point_of_sale.models';
import Registries from 'point_of_sale.Registries';
/**
 * NewPosGlobalState extends the PosGlobalState class to add custom message processing functionality.
 * Inherits from PosGlobalState.
 */
const NewPosGlobalState = (PosGlobalState) => class NewPosGlobalState extends PosGlobalState {
    async _processData(loadedData) {
        await super._processData(...arguments);
        this.pos_custom_message = loadedData['pos.custom.message'];
    }
}
// Extend the PosGlobalState model with the NewPosGlobalState functionality.
Registries.Model.extend(PosGlobalState, NewPosGlobalState);