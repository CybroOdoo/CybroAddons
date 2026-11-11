/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { Many2ManyTagsField } from "@web/views/fields/many2many_tags/many2many_tags_field";
patch(Many2ManyTagsField.prototype, {
    /**
     * Retrieves tag properties for the Many2ManyTagsField (Odoo 20 compatible).
     * In Odoo 20, tags are rendered via the BadgeTag component, so props must
     * match the badgeTagProps shape. We pass tooltipTemplate and tooltipInfo
     * as additional props that our BadgeTag template extension picks up.
     * @param {Object} record - The record for which tag properties are retrieved.
     * @returns {Object} Tag properties object.
     */
    getTagProps(record) {
        const field = this.props.record.fields[this.props.name];
        const info = {
            viewMode: "form",
            resModel: this.props.record.resModel,
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
            color: record.data[this.props.colorField],
            text: record.data.display_name || "",
            tooltip: record.data.display_name || "",
            onDelete: !this.props.readonly ? () => this.deleteTag(record.id) : undefined,
            onClick: (ev) => this.onTagClick(ev, record),
            // Custom props consumed by our web.BadgeTag template extension
            tooltipTemplate: "dynamic_hover_on_related_fields.RelatedFieldTooltip",
            tooltipInfo: JSON.stringify(info),
        };
    },
});
