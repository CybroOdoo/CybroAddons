/** @odoo-module **/

import { patch } from "@web/core/utils/patch"
import { ListRenderer } from "@web/views/list/list_renderer";

patch(ListRenderer.prototype, "ListRenderer_patch", {
    /**
     * Generate tooltip information for a field.
     * @param {Object} record - The record object.
     * @param {Object} fields - The fields object.
     * @returns {string} - JSON string containing tooltip information.
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
    },
    /**
     * Check if the field type is many2one.
     * @param {Object} record - The record object.
     * @param {Object} fields - The fields object.
     * @returns {boolean} - True if the field type is many2one, false otherwise.
     */
    isMany2one(record, fields){
        const field = record.fields[fields.name]
        return field.type === 'many2one';
    }
})