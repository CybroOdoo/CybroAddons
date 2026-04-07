/** @odoo-module **/
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { rpc } from "@web/core/network/rpc";
import { patch } from "@web/core/utils/patch";
import { CrossProduct } from "@pos_pro_cross_selling/app/cross_product/cross_product";

//Patching ProductScreen
patch(ProductScreen.prototype, {
    // Override addProductToOrder to show cross-selling popup after adding product
    async addProductToOrder(product, options = {}) {
        // Call original method - pass product object as product_tmpl_id (Odoo 19 pattern)
        var ProductSelected = await this.pos.addLineToCurrentOrder({ product_tmpl_id: product }, options);

        // Show optional products popup if needed (from original method)
//        this.showOptionalProductPopupIfNeeded(product);

        // Cross-selling logic
        if (ProductSelected && ProductSelected.raw && ProductSelected.raw.product_id) {
            rpc('/web/dataset/call_kw/pos.cross.selling/get_cross_selling_products', {
                model: 'pos.cross.selling',
                method: 'get_cross_selling_products',
                args: [[], ProductSelected.raw.product_id],
                kwargs: {},
            }).then(async (result) => {
                if (result && result.length > 0) {
                    await this.dialog.add(CrossProduct, {
                        product: result
                    });
                }
            });
        }
    },
});
