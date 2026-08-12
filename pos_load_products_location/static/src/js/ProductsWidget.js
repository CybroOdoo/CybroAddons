/** @odoo-module **/
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { patch } from "@web/core/utils/patch";
import { onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

patch(ProductScreen.prototype, {
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.notification = useService("notification");
        onWillStart(async () => {
            try {
                const productIds = await this.orm.call("stock.location", "search_products_by_location");
                if (!productIds || productIds.length === 0) {
                    this.notification.add("No products available in this location", {
                        type: "warning",
                    });
                    this.pos.setAllowedProductIds([]);
                } else {
                    this.pos.setAllowedProductIds(productIds);
                }
            } catch (error) {
                console.error("Failed to filter products by stock location", error);
                this.pos.setAllowedProductIds([]);
            }
        });
    },

    get productsToDisplay() {
        const list = super.productsToDisplay;
        if (this.pos._allowedProductIds === null) {
            return list;
        }
        if (this.pos._allowedProductIds.size === 0) {
            return [];
        }
        return list.filter((product) => this.pos._allowedProductIds.has(product.id));
    },
});