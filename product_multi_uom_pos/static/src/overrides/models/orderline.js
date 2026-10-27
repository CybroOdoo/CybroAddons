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
            // selected_uom_id is a proper Many2one field – restored automatically
            // by the related_models framework. No manual assignment needed.
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
        this.selected_uom_id = uomRecord.uom_id;  // integer ID of the chosen UoM

        this.custom_uom_name = uomRecord.uom_name;
        this.custom_uom_price = uomRecord.price;

        if (uomRecord.price !== undefined && uomRecord.price !== null) {
            this.setUnitPrice(uomRecord.price);
            // Set price_type = 'manual' so that setQuantity() does NOT
            // recompute the price when the user changes the quantity.
            this.price_type = "manual";
        }
    },

    reset_uom_to_default() {
        const product = this.product_id;
        const defId = Array.isArray(product.uom_id)
            ? product.uom_id[0]
            : (product.uom_id?.id || product.uom_id);
        this.product_uom_id = defId;
        // Clear the persisted selected UoM on the model field
        this.selected_uom_id = false;
        this.custom_uom_name = null;
        this.custom_uom_price = 0;
        this.setUnitPrice(product.lst_price);
        // Restore 'original' so pricelist rules and qty-driven price changes resume
        this.price_type = "original";
    },

    serialize() {
        // Used for IndexedDB / draft-order persistence. The live ORM sync path
        // uses ormSerialization which reads model fields directly (including
        // selected_uom_id), so this method is only needed for offline storage.
        const json = super.serialize(...arguments);
        return Object.assign(json, {
            product_uom_id: this.product_uom_id,
            custom_uom_name: this.custom_uom_name,
            custom_uom_price: this.custom_uom_price,
        });
    }
});