/** @odoo-module **/
import { registry } from "@web/core/registry";
import framework from 'web.framework';
import session from 'web.session';

registry.category("ir.actions.report handlers")
    .add("xlsx_handler", async function (action) {
    //Passing data to the controller to print the excel file
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
})
