/** @odoo-module **/
/**
 * Extends PosGlobalState and it extends Registries
 * Override the _processData method to process loaded data
 **/
import { PosGlobalState} from 'point_of_sale.models';
import Registries from 'point_of_sale.Registries';

const AnalyticAccount = (PosGlobalState) => class AnalyticAccount extends PosGlobalState {
    async _processData(loadedData) {
        await super._processData(...arguments);
        this.res_config_settings = loadedData['res.config.settings'];
        }
    }
Registries.Model.extend(PosGlobalState, AnalyticAccount);