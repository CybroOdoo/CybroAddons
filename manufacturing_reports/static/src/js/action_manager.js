//@odoo-modules

import { registry } from "@web/core/registry";
import framework from 'web.framework';
import session from 'web.session';

//report_type is added into a registry and checks  report_type is ‘XLSX.’Then call the corresponding controller function
registry.category("ir.actions.report handlers").add("xlsx", async (action) => {
	if (action.report_type === 'xlsx') {
    	framework.blockUI();
    	var def = $.Deferred();
    	session.get_file({
        	url: '/xlsx_reports',
        	data: action.data,
        	success: def.resolve.bind(def),
        	error: (error) => this.call('crash_manager', 'rpc_error', error),
        	complete: framework.unblockUI,
    	});
    	return def;
	}
})
