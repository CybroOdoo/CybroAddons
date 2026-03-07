/** @odoo-module */
import { PosStore } from "@point_of_sale/app/services/pos_store";
import { patch } from "@web/core/utils/patch";

patch(PosStore.prototype, {
    async setup() {
        await super.setup(...arguments);
        this._processMultiUomData();
    },

    _processMultiUomData() {
        const rawData = this.models["pos.multi.uom"]?.getAll() || [];

        this.multi_uoms_by_tmpl_id = {};

        for (const rec of rawData) {
            let tmplId = rec.product_template_id;
            if (typeof tmplId === 'object') tmplId = tmplId.id;
            if (Array.isArray(tmplId)) tmplId = tmplId[0];

            if (!this.multi_uoms_by_tmpl_id[tmplId]) {
                this.multi_uoms_by_tmpl_id[tmplId] = [];
            }

            let uomId = rec.uom_id;
            let uomName = "Unit";
            if (typeof uomId === 'object') {
                uomName = uomId.name || uomId.display_name;
                uomId = uomId.id;
            } else if (Array.isArray(uomId)) {
                uomName = uomId[1];
                uomId = uomId[0];
            }

            this.multi_uoms_by_tmpl_id[tmplId].push({
                id: rec.id,
                uom_id: uomId,
                uom_name: uomName,
                price: rec.price || 0
            });
        }
    }
});