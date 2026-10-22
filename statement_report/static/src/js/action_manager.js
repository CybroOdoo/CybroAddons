/** @odoo-module*/
import {registry} from "@web/core/registry";
import {download} from "@web/core/network/download";

// Action manager for xlsx report
registry.category('ir.actions.report handlers').add(
    'xlsx', async (action, options, env) => {
        if (action.report_type !== 'xlsx') {
            return false;
        }
        env.services.ui.block();
        try {
            await download({
                url: '/xlsx_report',
                data: action.data,
            });
        } finally {
            env.services.ui.unblock();
        }
        return true;
    });
