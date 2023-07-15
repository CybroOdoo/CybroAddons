/** @odoo-module **/
import {PosGlobalState} from 'point_of_sale.models';
import Registries from 'point_of_sale.Registries';

const CustomerTag = (PosGlobalState) => class CustomerTag extends PosGlobalState {
    /**
    load customer tag data to PosGlobalState
    **/
    async _processData(loadedData) {
        await super._processData(loadedData);
        this.customer_tag = loadedData['res.partner.category'];
    }
}
Registries.Model.extend(PosGlobalState, CustomerTag);