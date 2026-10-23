/** @odoo-module **/
import { registry } from "@web/core/registry";
import { download } from "@web/core/network/download";

registry.category("ir.actions.report handlers").add("qwerty_xlsx", async function (action) {
    if (action.report_type === 'xlsx') {
        await download({
            url: '/xlsx_reports',
            data: action.data,
        });
        return true;
    }
});
