/** @odoo-module **/
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { CrossProduct } from "@pos_pro_cross_selling/app/cross_product/cross_product";

//Patching ProductScreen
patch(ProductScreen.prototype, {
    setup() {
        super.setup();
        this.orm = useService("orm");
    },

    async addProductToOrder(product, ...args) {
        await super.addProductToOrder(product, ...args);
        const order = this.pos.getOrder();
        const selectedLine = order?.getSelectedOrderline();
        const productId = selectedLine?.product_id?.id || selectedLine?.raw?.product_id;

        if (productId) {
            try {
                const result = await this.orm.call("pos.cross.selling", "get_cross_selling_products", [productId]);
                if (result && result.length > 0) {
                    await this.dialog.add(CrossProduct, {
                        product: result
                    });
                }
            } catch {
                // Keep the product order flow available if cross-selling lookup fails.
            }
        }
    },
});
