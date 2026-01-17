/** @odoo-module **/

import { ListRenderer } from "@web/views/list/list_renderer";
import { patch } from "@web/core/utils/patch";

patch(ListRenderer.prototype, {
    toggleRecordSelection(record) {
        const result = super.toggleRecordSelection(...arguments);

        // Try to find the checkbox that triggered the selection
        const activeEl = document.activeElement;
        const selectedRecord = activeEl.closest("tr");

        if (activeEl && activeEl.type === "checkbox") {
            if (activeEl.checked) {
                selectedRecord.classList.add("selected_record");
            } else {
                selectedRecord.classList.remove("selected_record");
            }
        }

        return result;
    }
});
