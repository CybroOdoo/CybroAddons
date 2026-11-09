import { PosOrderline } from "@point_of_sale/app/models/pos_order_line";
import { patch } from "@web/core/utils/patch";

patch(PosOrderline.prototype, {
    /**
     * Odoo 20: setup(vals) receives a single vals dict.
     * Fields declared in Python (custom_uom_name, custom_uom_price, product_uom_id)
     * are already populated on `this` by the model framework before setup() runs.
     * No manual initialisation from options.json is needed.
     */
    setup(vals) {
        super.setup(vals);
    },

    /**
     * Apply a custom UoM selection from the POS UI.
     * @param {Object} uomRecord - { uom_id, uom_name, price }
     */
    set_custom_uom(uomRecord) {
        if (!uomRecord) return;
        this.product_uom_id = uomRecord.uom_id;
        this.custom_uom_name = uomRecord.uom_name;
        this.custom_uom_price = uomRecord.price;
        if (uomRecord.price > 0) {
            this.setUnitPrice(uomRecord.price);
            this.price_manually_set = true;
        }
    },

    /**
     * Reset the order line back to the product's default UoM.
     */
    reset_uom_to_default() {
        const product = this.product_id;
        this.product_uom_id = product?.uom_id || null;
        this.custom_uom_name = null;
        this.custom_uom_price = 0;
        this.setUnitPrice(product?.lst_price || 0);
        this.price_manually_set = false;
    },
});
