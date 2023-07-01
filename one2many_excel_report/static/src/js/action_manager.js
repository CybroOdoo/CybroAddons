/** @odoo-module */
import { registry } from "@web/core/registry";
import framework from 'web.framework';
import session from 'web.session';
registry.category("ir.actions.report handlers").add("xlsx", async (action) => {
//This is used to check the report type
   if (action.report_type === 'xlsx') {
       framework.blockUI();
       var self = this;
       var def = $.Deferred();
       session.get_file({
           url: '/xlsx_reports',
           data: {'id':action.context.id,'field':action.context.field,'current_model':action.context.model},
           success: def.resolve.bind(def),
           complete: framework.unblockUI,
       });
       return def;
   }
});