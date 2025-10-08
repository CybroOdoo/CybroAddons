/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { Many2ManyTagsField } from "@web/views/fields/many2many_tags/many2many_tags_field";

patch(Many2ManyTagsField.prototype, "Many2ManyTagsField_patch", {

    /**
     * Retrieves tag properties for the Many2ManyTagsField.
     * @param {Object} record - The record for which tag properties are retrieved.
     * @returns {Object} Tag properties object.
     */
    getTagProps(record) {
        const field = this.props.record.fields[this.props.name]
        const info = {
            viewMode: "form",
            resModel:this.props.record.resModel,
            resId: this.props.record.resId,
            related_record_id: record.resId,
            debug: Boolean(odoo.debug),
            field: {
                name: field.name,
                help: field?.help,
                type: field.type,
                domain: field.domain,
                relation: field.relation,
            },
        };
        return {
            id: record.id, // datapoint_X
            resId: record.resId,
            text: record.data.display_name,
            colorIndex: record.data[this.props.colorField],
            onDelete: !this.props.readonly ? () => this.deleteTag(record.id) : undefined,
            onKeydown: this.onTagKeydown.bind(this),
            info: JSON.stringify(info)
        };
    }
})
