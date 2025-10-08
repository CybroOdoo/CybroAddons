/** @odoo-module **/

import { PosGlobalState } from 'point_of_sale.models';
import Registries from 'point_of_sale.Registries';

const VariantsPosGlobalState = (PosGlobalState) => class VariantsPosGlobalState extends PosGlobalState {
    async _processData(loadedData) {

        await super._processData(...arguments);

        this.variants_tree = loadedData['variants.tree'];
        this.product_attribute_value = loadedData['product.attribute.value'];
    }
}
Registries.Model.extend(PosGlobalState, VariantsPosGlobalState);
