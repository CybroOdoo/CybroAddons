/** @odoo-module **/

import { Orderline } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";

/**
 * Patch the Orderline model to support storing and persisting
 * product_variants data selected via the multi-variant popup.
 */
patch(Orderline.prototype, {
    setup(_defaultObj, options) {
        super.setup(...arguments);
        this.product_variants = options.json?.product_variants || [];
    },

    init_from_JSON(json) {
        super.init_from_JSON(...arguments);
        this.product_variants = json.product_variants || [];
    },

    export_as_JSON() {
        const json = super.export_as_JSON(...arguments);
        json.product_variants = this.product_variants || [];
        return json;
    },

    export_for_printing() {
        const result = super.export_for_printing(...arguments);
        result.product_variants = this.product_variants || [];
        return result;
    },

    getDisplayData() {
        return {
            ...super.getDisplayData(),
            product_variants: this.product_variants || [],
        };
    },
});
