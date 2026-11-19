/** @odoo-module **/

import { registry } from "@web/core/registry";
import { download } from "@web/core/network/download";

registry.category("ir.actions.report handlers").add("low_sale_xlsx_download", async function (action) {
    if (action.report_type === "low_sale_xlsx_download") {
        await download({
            url: "/sale_low_xlsx_reports",
            data: action.data,
        });
        return true;
    }
});
