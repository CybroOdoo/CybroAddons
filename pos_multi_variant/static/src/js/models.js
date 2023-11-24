odoo.define('pos_multi_variant.model', function(require) {
    'use strict';
     /* This JavaScript code defines the VariantsPosGlobalState class
     * extending the PosGlobalState class from the point_of_sale.models module.
     * It adds additional functionality to process variants data.
     */
    var {
        PosGlobalState
    } = require('point_of_sale.models');
    const Registries = require('point_of_sale.Registries');
    const VariantsPosGlobalState = (PosGlobalState) => class VariantsPosGlobalState extends PosGlobalState {
        async _processData(loadedData) {

            await super._processData(...arguments);

            this.variants_tree = loadedData['variants.tree'];
            this.product_attribute_value = loadedData['product.attribute.value'];
        }
    }
    Registries.Model.extend(PosGlobalState, VariantsPosGlobalState);
});
