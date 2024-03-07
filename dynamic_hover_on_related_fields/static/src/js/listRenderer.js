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
            resModel: record.resModel,
            related_record_id: record.data[fields.name][0],
            resId: record.resId,
            debug: Boolean(odoo.debug),
            field: {
                name: field.name,
                help: field?.help,
                type: field.type,
                domain: field.domain,
                relation: field.relation,
            },
        };
        return JSON.stringify(info);
    }
})