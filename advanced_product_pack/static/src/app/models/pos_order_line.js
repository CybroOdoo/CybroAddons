/** @odoo-module **/
/** Add product-pack component details to POS order-line display data. */

import { Orderline } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";

patch(Orderline.prototype, {
    _getBundleDetails() {
        /** Return parsed component data, or an empty list when it is unavailable. */
        const product = this.get_product ? this.get_product() : this.product_id;
        if (product && product.is_bundle && product.bundle_contents_info) {
            try {
                return typeof product.bundle_contents_info === "string"
                    ? JSON.parse(product.bundle_contents_info)
                    : product.bundle_contents_info;
            } catch (e) {
                console.error("Error parsing bundle details", e);
                return [];
            }
        }
        return [];
    },

    getDisplayData() {
        /** Extend the standard display payload with product-pack state and contents. */
        const data = super.getDisplayData(...arguments);
        const product = this.get_product ? this.get_product() : this.product_id;
        if (product && product.is_bundle) {
            data.bundleDetails = this._getBundleDetails();
            data.is_bundle = true;
        } else {
            data.bundleDetails = [];
            data.is_bundle = false;
        }
        return data;
    },
});
