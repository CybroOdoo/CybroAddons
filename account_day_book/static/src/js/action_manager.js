/** @odoo-module **/

import { registry } from "@web/core/registry";
import { download } from "@web/core/network/download";

registry.category("ir.actions.report handlers").add("account_day_book_xlsx", async (action, options, env) => {
    if (action.report_type === 'day_xlsx_download') {
        env.services.ui.block();
        try {
            await download({
                url: '/day_xlsx_reports',
                data: action.data,
            });
            return true;
        } finally {
            env.services.ui.unblock();
        }
    }
});
