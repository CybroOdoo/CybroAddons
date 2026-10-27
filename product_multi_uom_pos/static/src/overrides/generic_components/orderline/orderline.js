/** @odoo-module */
import { Orderline } from "@point_of_sale/app/components/orderline/orderline";
import { OrderSummary } from "@point_of_sale/app/screens/product_screen/order_summary/order_summary";
import { patch } from "@web/core/utils/patch";

patch(OrderSummary.prototype, {
    async onOrderlineLongPress(ev, orderline) {
        const customUomPrice = orderline?.custom_uom_price;
        const res = await super.onOrderlineLongPress(...arguments);
        if (customUomPrice && orderline?.custom_uom_name) {
            orderline.price_unit = customUomPrice;
            orderline.price_type = "manual";
        }
        return res;
    },
});

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

    getCurrentSelectedUomId() {
        const line = this.props.line;
        if (!line || !line.custom_uom_name) return null;
        return line.selected_uom_id?.id || line.selected_uom_id || line.product_uom_id || null;
    },

    onUomChange(event) {
        if (!event.target.value) {
            // User selected "Change Uom" placeholder or empty; restore select to current UoM without resetting price
            const currentId = this.getCurrentSelectedUomId();
            if (currentId) {
                event.target.value = currentId;
            }
            return;
        }
        const selectedId = parseInt(event.target.value);
        const uomRecord = this.getAvailableUoms().find(u => u.uom_id === selectedId);
        if (uomRecord) {
            this.props.line.set_custom_uom(uomRecord);
        } else {
            console.error("❌ [UI] Could not find UoM record for ID:", selectedId);
        }
    },

    get lineScreenValues() {
        const vals = super.lineScreenValues;
        const line = this.line;
        if (!line || !vals) {
            return vals;
        }
        const uomName =
            line.custom_uom_name ||
            line.selected_uom_id?.name ||
            (typeof line.selected_uom_id === "number" && line.models?.["uom.uom"]?.get(line.selected_uom_id)?.name) ||
            line.getUnit()?.name ||
            line.product_id?.product_tmpl_id?.uom_id?.name ||
            line.product_id?.uom_id?.name ||
            "";

        const basic = this.props.basic_receipt;
        const mode = this.props.mode;
        const showPrice =
            !basic &&
            (line.getQuantityStr() != 1 || Boolean(line.custom_uom_name)) &&
            (mode === "receipt" || (line.price_type !== "original" && !line.combo_parent_id));

        if (showPrice && line.price !== 0 && uomName) {
            vals.displayPriceUnit = `${line.currencyDisplayPriceUnit} / ${uomName}`;
        }
        return vals;
    },

    getCurrentUomDisplay() {
        const line = this.props.line;
        const display = {
            price: line.custom_uom_price || line.price_unit,
            uomName: line.custom_uom_name || line.product_id?.uom_id?.name || "Unit"
        };
        return display;
    },

    onReset() {
        this.props.line.reset_uom_to_default();
    }
});