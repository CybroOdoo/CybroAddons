/** @odoo-module */
import { registry } from "@web/core/registry";
import framework from 'web.framework';
import session from 'web.session';

registry.category("ir.actions.report handlers").add("xlsx", async (action) => {
    /*It is to pass data to the controller for printing xlsx report.*/
    if (action.report_type === 'xlsx') {
        framework.blockUI();
        var def = $.Deferred();
        session.get_file({
            url: '/xlsx_reports',
            data: action.data,
            success: def.resolve.bind(def),
            complete: framework.unblockUI,
        });
        return def;
    }
});
