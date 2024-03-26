/** @odoo-module **/
import { ListRenderer } from "@web/views/list/list_renderer";
import { patch } from "@web/core/utils/patch";
/**
 * Patched function to toggle record selection and add a CSS class to selected records.
 *
 * @param {Object} record - The record to toggle selection for.
 */
patch(ListRenderer.prototype, {
    toggleRecordSelection(record, ev)  {
        var self = this;
        const result = super.toggleRecordSelection(...arguments);
        var selectedRecord = $(event.target).closest('tr')
        if ($(event.target).prop('checked')) {
            selectedRecord.addClass('selected_record');
        } else {
            selectedRecord.removeClass('selected_record')
        }
        return result
    }
});
