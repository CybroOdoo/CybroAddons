/** @odoo-module **/

import { patch } from "@web/core/utils/patch"
import { ListRenderer } from "@web/views/list/list_renderer";

patch(ListRenderer.prototype, {
    /**
     * Generates tooltip information for the ListRenderer.
     * @returns {string} JSON string representing tooltip information.
     */
    tolTipInfo(record, fields) {
        const field = record.fields[fields.name]
        const info = {
                viewMode: "list",
                related_record_id: record.data[fields.name][0],
                relation: field.relation,
            }
        return JSON.stringify(info);
    },
    checkModel(record, fields){
        const field = record.fields[fields.name]
        return ['product.template', 'product.product'].includes(field.relation)
    }

})