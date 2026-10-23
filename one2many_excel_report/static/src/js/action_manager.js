/** @odoo-module */
import { registry } from "@web/core/registry";
import { download } from "@web/core/network/download";
/**
This handler is responsible for generating XLSX reports.
*/
registry.category("ir.actions.report handlers").add("xlsx", async function (action) {
    if (action.report_type === 'xlsx') {
        await download({
            url: '/xlsx_reports',
            data: {
                id: action.context.id,
                field: action.context.field,
                current_model: action.context.model,
            },
        });
        return true;
    }
});
