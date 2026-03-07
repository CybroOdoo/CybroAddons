/** @odoo-module */
import { Orderline } from "@point_of_sale/app/components/orderline/orderline";
import { patch } from "@web/core/utils/patch";

patch(Orderline.prototype, {
    getAvailableUoms() {
        const line = this.props.line;
        if (!line || !line.product_id) return [];

        const pos = this.env.services.pos;
        const product = line.product_id;

        let tmplId = product.product_tmpl_id;
        if (tmplId && typeof tmplId === 'object') tmplId = tmplId.id;
        if (Array.isArray(tmplId)) tmplId = tmplId[0];

        const uoms = pos.multi_uoms_by_tmpl_id?.[tmplId] || [];
        return uoms;
    },

    onUomChange(event) {
        const selectedId = parseInt(event.target.value);
        const uomRecord = this.getAvailableUoms().find(u => u.uom_id === selectedId);
        if (uomRecord) {
            this.props.line.set_custom_uom(uomRecord);
        } else {
            console.error("❌ [UI] Could not find UoM record for ID:", selectedId);
        }
    },

    getCurrentUomDisplay() {
        const line = this.props.line;
        const display = {
            price: line.custom_uom_price || line.price_unit,
            uomName: line.custom_uom_name || line.uom?.name || "Unit"
        };
        return display;
    },

    onReset() {
        this.props.line.reset_uom_to_default();
    }
});