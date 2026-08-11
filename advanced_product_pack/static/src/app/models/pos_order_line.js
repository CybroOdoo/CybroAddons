import { PosOrderline } from "@point_of_sale/app/models/pos_order_line";
import { patch } from "@web/core/utils/patch";

patch(PosOrderline.prototype, {
    get bundleDetails() {
        if (this.product_id.is_bundle && this.product_id.bundle_contents_info) {
            try {
                return JSON.parse(this.product_id.bundle_contents_info);
            } catch (e) {
                console.error("Error parsing bundle details", e);
                return [];
            }
        }
        return [];
    }
});
