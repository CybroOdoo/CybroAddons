/** @odoo-module*/
import {registry} from "@web/core/registry";
var framework = require('web.framework')
var session = require('web.session')
/*Action manager for xlsx report*/
registry.category('ir.actions.report handlers').add('xlsx', async (action) => {
    if (action.report_type === 'xlsx'){
        framework.blockUI();
        var def = $.Deferred();
        session.get_file({
            url : '/xlsx_report',
            data : action.data,
            success : def.resolve.bind(def),
            error : (error) => this.call('crash_manager', 'rpc_error', error),
            complete : framework.unblockUI,
        });
        return def;
    }
})
