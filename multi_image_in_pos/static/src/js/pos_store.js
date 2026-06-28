/** @odoo-module */

import { PosStore } from "@point_of_sale/app/services/pos_store";
import { ProductInfoPopup } from "@point_of_sale/app/components/popups/product_info_popup/product_info_popup";
import { patch } from "@web/core/utils/patch";

patch(PosStore.prototype, {
    async onProductInfoClick(productTemplate, productProduct = false) {
        if (this.config.enable_multi_image){
            let productVariant = productProduct;

            if (!productVariant) {
                const selectedOrder = this.selectedOrder;
                if (selectedOrder) {
                    const selectedLine = selectedOrder.getSelectedOrderline();
                    if (selectedLine) {
                        const lineProduct = selectedLine.getProduct();
                        if (lineProduct.raw.product_tmpl_id === productTemplate.id) {
                            productVariant = lineProduct;
                        }
                    }
                }
            }

            if (!productVariant && productTemplate.product_variant_ids && productTemplate.product_variant_ids.length > 0) {
                productVariant = productTemplate.product_variant_ids[0];
            }

            const info = await this.getProductInfo(productTemplate, 1, 0, productVariant);
            this.dialog.add(ProductInfoPopup, {
                info: info,
                productTemplate: productTemplate,
                product: productVariant || false
            });
        } else {
           return super.onProductInfoClick(...arguments);
        }
    }
});
