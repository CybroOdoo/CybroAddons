/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { Many2One } from "@web/views/fields/many2one/many2one";
import { Many2OneField } from "@web/views/fields/many2one/many2one_field";

patch(Many2One.prototype, {
     /**
     * Generates tooltip information for the Many2OneField.
     * @returns {string} JSON string representing tooltip information.
     */
     setup() {
        super.setup();
    },
    get tooltipInfo() {
        const relationValue = this.props.value;
        const relatedId = relationValue?.id || false;

        const info = {
            viewMode: "form",
            resModel: this.props.relation,
            resId: relatedId,
            related_record_id: relatedId,
            debug: Boolean(odoo.debug),
            field: {
                name: this.props.id,
                type: "many2one",
                relation: this.props.relation,
            },
        };

        return JSON.stringify(info);
    },
});
