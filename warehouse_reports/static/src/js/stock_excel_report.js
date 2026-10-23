import { download } from "@web/core/network/download";
import { registry } from "@web/core/registry";

registry.category("ir.actions.report handlers").add("qwerty_xlsx", async (action) => {
    if (action.report_type === 'xlsx') {
        await download({
            url: '/xlsx_reports',
            data: action.data,
        });
        return true;
    }
});