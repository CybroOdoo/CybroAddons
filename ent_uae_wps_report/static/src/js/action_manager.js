/** @odoo-module */
import { registry } from "@web/core/registry";
import { download } from "@web/core/network/download";
import { Deferred } from "@web/core/utils/concurrency";
import { BlockUI } from "@web/core/ui/block_ui";

registry.category("ir.actions.report handlers").add('xlsx', async function(action,option,env) {
    if (action.report_type === 'wps_xlsx') {
         BlockUI;
        var def = new Deferred();
        await download({
            url: '/xlsx_reports',
            data: action.data,
            success: def.resolve.bind(def),
            complete: () => unblockUI,
        });
    }
});
