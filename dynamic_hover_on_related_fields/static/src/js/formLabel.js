/** @odoo-module **/

import { FormLabel } from "@web/views/form/form_label"
import { patch } from "@web/core/utils/patch"
import { getTooltipInfo } from "./fieldToltip"
patch(FormLabel.prototype, {

    /**
     * Retrieves tooltip information for the FormLabel.
     * @returns {string} JSON string representing tooltip information.
     */
    get tooltipInfo() {
        if (!odoo.debug) {
            return JSON.stringify({
                field: {
                    help: this.tooltipHelp,
                },
            });
        }
        return getTooltipInfo({
            viewMode: "form",
            resModel: this.props.record.resModel,
            resId: this.props.record.resId,
            field: this.props.record.fields[this.props.fieldName],
            fieldInfo: this.props.fieldInfo,
            help: this.tooltipHelp,
        });
    },
})