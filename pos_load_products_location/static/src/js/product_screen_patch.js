import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { patch } from "@web/core/utils/patch";
import { onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

patch(ProductScreen.prototype, {
    /**
     * Loads the product ids of the configured stock location when the product screen starts.
     *
     **/
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.notification = useService("notification");
        onWillStart(async () => {
            try {
                const productIds = await this.orm.call("stock.location", "search_products_by_location");
                if (productIds === false || productIds === null) {
                    this.pos.setAllowedProductIds(null);
                } else if (Array.isArray(productIds) && productIds.length === 0) {
                    this.notification.add(_t("No products available in this location"), {
                        type: "warning"
                    });
                    this.pos.setAllowedProductIds([]);
                } else {
                    this.pos.setAllowedProductIds(productIds);
                }
            } catch (error) {
                console.error("Failed to filter products by stock location", error);
                this.pos.setAllowedProductIds(null);
            }
        });
    }
});
