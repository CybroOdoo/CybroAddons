/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { Order } from "@point_of_sale/app/store/models";
import { PosStore } from "@point_of_sale/app/store/pos_store";

patch(PosStore.prototype, {
    async addProductToCurrentOrder(product, options = {}) {
            var product = product
            var options = options
            if(this.env.services.pos.config.is_allow_manual_weight && product.to_weight){
                    // Show the ScaleScreen to weigh the product.
                     const { confirmed, payload } = await this.showTempScreen('ScaleScreen', {
                            product,
                     });
                     if (confirmed) {
                           options['quantity'] = payload.weight
                           this.addProductFromUi(product, options);
                     } else {
                            // do not add the product;
                        return;
                     }
            }
            else{
            // add product if allow manual button is not enabled in the settings.
            await this.addProductFromUi(product, options);
            }
            // Do not add product if options is undefined.
            if (!options) return;
            // Add the product after having the extra information.
    }
})
