/** @odoo-module */
import { PosOrderline } from "@point_of_sale/app/models/pos_order_line";
import { patch } from "@web/core/utils/patch";

patch(PosOrderline.prototype, {
    setup(defaultObj, options) {
        super.setup(...arguments);
        this.custom_uom_name = this.custom_uom_name || null;
        this.custom_uom_price = this.custom_uom_price || 0;

        if (options && options.json) {
            this.custom_uom_name = options.json.custom_uom_name || null;
            this.custom_uom_price = options.json.custom_uom_price || 0;
            if (options.json.product_uom_id) {
                this.product_uom_id = options.json.product_uom_id;
            }
        }
    },

    get canBeRemoved() {
        try {
            const uom = this.product_id?.uom_id;
            if (uom && typeof uom.isZero === 'function') {
                return uom.isZero(this.qty);
            }
        } catch (e) {
            // Ignore error
        }
        return Math.abs(this.qty) < 0.0001;
    },

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

    reset_uom_to_default() {
        const product = this.product_id;
        const defId = Array.isArray(product.uom_id) ? product.uom_id[0] : (product.uom_id?.id || product.uom_id);
        this.product_uom_id = defId;
        this.custom_uom_name = null;
        this.custom_uom_price = 0;
        this.setUnitPrice(product.lst_price);
        this.price_manually_set = false;
    },

    serialize() {
        const json = super.serialize(...arguments);
        return Object.assign(json, {
            product_uom_id: this.product_uom_id,
            custom_uom_name: this.custom_uom_name,
            custom_uom_price: this.custom_uom_price
        });
    }
});