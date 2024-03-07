/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { Many2OneField } from "@web/views/fields/many2one/many2one_field";

patch(Many2OneField.prototype, {
    /**
     * Generates tooltip information for the Many2OneField.
     * @returns {string} JSON string representing tooltip information.
     */
    get tooltipInfo() {
        return this.getTooltipInfo({
            viewMode: "form",
            resModel: this.props.record.resModel,
            related_record_id: this.props.record.data[this.props.name][0],
            resId: this.props.record.resId,
            field: this.props.record.fields[this.props.name],
            fieldInfo: this.props.fieldInfo,
        });

    },

    /**
     * Constructs tooltip information object based on provided parameters.
     * @param {Object} params - Parameters for tooltip information.
     * @param {string} params.viewMode - View mode of the record.
     * @param {string} params.resModel - Model of the record.
     * @param {number} params.resId - ID of the record.
     * @param {Object} params.field - Field information.
     * @param {Object} params.fieldInfo - Field information.
     * @returns {string} JSON string representing tooltip information.
     */
    getTooltipInfo(params){
        const info = {
            viewMode: params.viewMode,
            resModel: params.resModel,
            related_record_id: params.related_record_id,
            resId: params.resId,
            debug: Boolean(odoo.debug),
            field: {
                name: params.field.name,
                help: params.field?.help,
                type: params.field.type,
                domain: params.field.domain,
                relation: params.field.relation,
            },
        };
        return JSON.stringify(info);
    },
})