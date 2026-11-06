import { PosStore } from "@point_of_sale/app/services/pos_store";
import { patch } from "@web/core/utils/patch";

patch(PosStore.prototype, {
    _allowedProductIds: null,
    productFilterKey: 0,
    setAllowedProductIds(productIds) {
        if (productIds === null || productIds === undefined) {
            this._allowedProductIds = null;
        } else if (!Array.isArray(productIds) || productIds.length === 0) {
            this._allowedProductIds = new Set();
        } else {
            this._allowedProductIds = new Set(productIds);
        }
        this.productFilterKey++;
    },

    get productsToDisplay() {
        this.productFilterKey; // read to subscribe to filter changes
        const list = super.productsToDisplay;
        if (this._allowedProductIds === null) {
            return list;
        }
        if (this._allowedProductIds.size === 0) {
            return [];
        }
        return list.filter((product) => this._allowedProductIds.has(product.id));
    },
});
