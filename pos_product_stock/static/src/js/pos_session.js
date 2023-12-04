/** @odoo-module */
import {PosGlobalState} from 'point_of_sale.models';
import Registries from 'point_of_sale.Registries';
const NewPosGlobalState = (PosGlobalState) =>
    class NewPosGlobalState extends PosGlobalState { // Define a new class that extends the PosGlobalState model.
        // Then, add a new method called '_processData'.
        async _processData(loadedData) {
            await super._processData(...arguments); //used to call the original _processData
            this.res_setting = loadedData['res.config.settings'];
            this.stock_quant = loadedData['stock.quant'];
            this.move_line = loadedData['stock.move.line'];
        }
    }
Registries.Model.extend(PosGlobalState, NewPosGlobalState);
