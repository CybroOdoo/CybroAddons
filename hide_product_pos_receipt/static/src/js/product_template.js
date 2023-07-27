odoo.define('hide_product_pos_receipt.models', function (require) {
    "use strict";
    var { PosGlobalState, Order} = require('point_of_sale.models');
    const Registries = require('point_of_sale.Registries');
    //Extending the models and load the product template new fields
    const PosSessionHideProduct = (PosGlobalState) => class PosSessionHideProduct extends PosGlobalState {
    async _processData(loadedData) {
        await super._processData(...arguments);
        this.product_template = loadedData['product.product'];
        }
    }
    Registries.Model.extend(PosGlobalState, PosSessionHideProduct);
});