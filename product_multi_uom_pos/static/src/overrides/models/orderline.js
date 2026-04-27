/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { PosOrderline } from "@point_of_sale/app/models/pos_order_line";
import { PosOrder } from "@point_of_sale/app/models/pos_order";

patch(PosOrderline.prototype, {
    setup(vals) {
        let res = super.setup(...arguments);
        // Initialize uom_id into raw
        if (!('uom_id' in this.raw)) {
            this.raw.uom_id = vals?.uom_id || null;
        }
        return res;
    },

    // For loading all selected multiple uom in pos
    getUom() {
        let pos_multi_uom = [];
        if (this.product_id?.pos_multi_uom_ids?.length > 0 &&
            this.product_id.pos_multi_uom_ids[0]?.category_id) {
            const filteredData = this.product_id.pos_multi_uom_ids;
            for (let uom of filteredData) {
                pos_multi_uom.push(uom.serialize());
            }
        }
        return pos_multi_uom;
    },

    getDisplayData() {
        const selectedUomId = this.raw?.uom_id || this.product_id?.uom_id?.id;
        // Find the uom name from pos_multi_uom data
        const uomRecord = this.models['uom.uom']?.get(selectedUomId);
        const uomName = uomRecord?.name || this.product_id?.uom_id?.name || "";
        return {
            ...super.getDisplayData(),
            getUom: this.getUom(),
            uom_id: this.raw?.uom_id || this.product_id?.uom_id?.id,
            unit_display: uomName,
            uuid: this.uuid,
        }
    },

     serialize() {
        const result = super.serialize(...arguments);
        result.uom_id = this.raw.uom_id || this.product_id?.uom_id?.id;
        return result;
    },

});

patch(PosOrder.prototype, {
    export_for_printing(baseUrl, headerData) {
        var result = super.export_for_printing(...arguments);
        if (result.orderlines) {
            result.orderlines = result.orderlines.map(({ onSelectionChangedUom, ...rest }) => rest);
        }
        return result;
    },
});
