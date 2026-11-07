/** @odoo-module **/
import { registry } from "@web/core/registry";
import { download } from "@web/core/network/download";

registry.category("ir.actions.report handlers").add("advanced_excel_reports_xlsx", async (action, options, env) => {
    // Passing data to the controller to print the excel file
    if (action.report_type === 'xlsx') {
        env?.services?.ui?.block();
        try {
            await download({
                url: '/xlsx_reports',
                data: action.data,
            });
        } finally {
            env?.services?.ui?.unblock();
        }
        return true;
    }
});
