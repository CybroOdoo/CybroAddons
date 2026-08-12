/** @odoo-module **/
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { patch } from "@web/core/utils/patch";

patch(PosStore.prototype, {
    _allowedProductIds: null,

    setAllowedProductIds(productIds) {
        if (!productIds || !Array.isArray(productIds)) {
            this._allowedProductIds = new Set();
        } else {
            this._allowedProductIds = new Set(productIds);
        }
    },
});