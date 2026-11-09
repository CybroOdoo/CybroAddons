import { PosStore } from "@point_of_sale/app/services/pos_store";
import { ComboSuggestion } from "@point_of_sale/app/models/utils/combo_suggestion";
import { patch } from "@web/core/utils/patch";

/**
 * Guard `_getProductOrderMap` and `getApplicableProductCombo` against receiving
 * an undefined/null order.  This can happen when our reactive UoM field changes
 * fire while the POS is on the standby screen (selectedOrderUuid === null →
 * pos.getOrder() returns undefined), causing the core `potentialCombos` computed
 * to crash on `order.unsentLines`.
 */
patch(ComboSuggestion.prototype, {
    _getProductOrderMap(order) {
        if (!order) return {};
        return super._getProductOrderMap(order);
    },

    getApplicableProductCombo(order, mode = "limited") {
        if (!order) return [];
        return super.getApplicableProductCombo(order, mode);
    },
});

patch(PosStore.prototype, {
    /**
     * Called by initServerData() after all POS model data has been loaded.
     * This is the correct Odoo 20 hook to post-process loaded records.
     */
    async afterProcessServerData() {
        const result = await super.afterProcessServerData(...arguments);
        this._processMultiUomData();
        return result;
    },

    /**
     * Build a lookup map: product_template_id → list of UoM options.
     * Stored as this.multi_uoms_by_tmpl_id for use by the Orderline component.
     */
    _processMultiUomData() {
        const rawData = this.models["pos.multi.uom"]?.getAll() || [];
        this.multi_uoms_by_tmpl_id = {};

        for (const rec of rawData) {
            // product_template_id may be a recordset object or a plain id
            let tmplId = rec.product_template_id;
            if (tmplId && typeof tmplId === "object") {
                tmplId = Array.isArray(tmplId) ? tmplId[0] : (tmplId.id ?? tmplId);
            }
            if (!tmplId) continue;

            if (!this.multi_uoms_by_tmpl_id[tmplId]) {
                this.multi_uoms_by_tmpl_id[tmplId] = [];
            }

            // uom_id may be a recordset object, a [id, name] pair, or a plain id
            let uomId = rec.uom_id;
            let uomName = "Unit";
            if (uomId && typeof uomId === "object") {
                if (Array.isArray(uomId)) {
                    uomName = uomId[1] || uomName;
                    uomId = uomId[0];
                } else {
                    uomName = uomId.name || uomId.display_name || uomName;
                    uomId = uomId.id;
                }
            }

            this.multi_uoms_by_tmpl_id[tmplId].push({
                id: rec.id,
                uom_id: uomId,
                uom_name: uomName,
                price: rec.price || 0,
            });
        }
    },
});
