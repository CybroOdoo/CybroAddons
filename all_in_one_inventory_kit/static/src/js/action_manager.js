/** @odoo-module */
import { registry } from "@web/core/registry";
import { BlockUI } from "@web/core/ui/block_ui";
import { download } from "@web/core/network/download";
// This function is responsible for generating and downloading an XLSX report.
registry.category("ir.actions.report handlers").add("stock_xlsx", async function (action){
    if (action.report_type === 'stock_xlsx') {
        const blockUI = new BlockUI();
        await download({
            url: '/xlsx_reports',
            data: action.data,
            complete: () => unblockUI,
            error: (error) => self.call('crash_manager', 'rpc_error', error),
        });
    }
});
//import framework from 'web.framework';
//import session from 'web.session';
//registry.category("ir.actions.report handlers").add("stock_xlsx", async (action) => {
//    if (action.report_type === 'stock_xlsx') {
//        framework.blockUI();
//        var def = $.Deferred();
//        session.get_file({
//            url: '/xlsx_reports',
//            data: action.data,
//            success: def.resolve.bind(def),
//            error: (error) => this.call('crash_manager', 'rpc_error', error),
//            complete: framework.unblockUI,
//        });
//        return def;
//    }
//});
