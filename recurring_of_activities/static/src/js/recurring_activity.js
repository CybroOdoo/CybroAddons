/** @odoo-module **/
import { registerPatch } from '@mail/model/model_core';
//patching and added the manage recurring button
registerPatch({
    name: 'ActivityMenuView',
    recordMethods: {
         onClickCustomLink(ev) {
         this.env.services.action.doAction({
             name: "Recurring Activities",
             type: 'ir.actions.act_window',
             res_model: 'recurring.activity',
             view_type: 'list',
             views: [[false, 'list'], [false, 'form']],
             target: 'current',
             context: {create: true}
         });
     },
    }
});
