import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { formatCurrency } from "@web/core/currency";
import { Orderline } from "@point_of_sale/app/components/orderline/orderline";
import { patch } from "@web/core/utils/patch";


patch(Orderline.prototype, {
    formatCurrency,

    setup() {
        super.setup(...arguments);
        // usePos() gives access to the PosStore (and multi_uoms_by_tmpl_id)
        this.pos = usePos();
    },

    /**
     * Return the list of custom UoM options for the current order line's product.
     * @returns {Array<{id, uom_id, uom_name, price}>}
     */
    getAvailableUoms() {
        const line = this.line;
        if (!line || !line.product_id) return [];

        const product = line.product_id;
        let tmplId = product.product_tmpl_id;
        if (tmplId && typeof tmplId === "object") {
            tmplId = Array.isArray(tmplId) ? tmplId[0] : (tmplId.id ?? tmplId);
        }

        return this.pos.multi_uoms_by_tmpl_id?.[tmplId] || [];
    },

    /**
     * Handle UoM dropdown change event.
     */
    onUomChange(event) {
        const value = event.target.value;
        if (!value) return;
        const selectedId = parseInt(value);
        const uomRecord = this.getAvailableUoms().find((u) => u.uom_id === selectedId);
        if (uomRecord) {
            this.line.set_custom_uom(uomRecord);
        } else {
            console.error("❌ [UoM] Could not find UoM record for ID:", selectedId);
        }
    },

    /**
     * Return the currently displayed UoM name and price for this line.
     */
    getCurrentUomDisplay() {
        const line = this.line;
        return {
            price: line.custom_uom_price || line.price_unit,
            uomName: line.custom_uom_name || line.product_id?.uom_id?.name || "Unit",
        };
    },

    /**
     * Extend the display values with custom UoM price-per-unit label.
     */
    get lineScreenValues() {
        const vals = super.lineScreenValues;
        const line = this.line;
        if (line && line.custom_uom_name && vals && vals.displayPriceUnit) {
            vals.displayPriceUnit = `${line.currencyDisplayPriceUnit} / ${line.custom_uom_name}`;
        }
        return vals;
    },

    /**
     * Reset the order line back to the product's default UoM.
     */
    onReset() {
        this.line.reset_uom_to_default();
    },
});
