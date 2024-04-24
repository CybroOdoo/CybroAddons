/** @odoo-module **/
import { ActivityMenu } from "@mail/core/web/activity_menu";
import { patch } from "@web/core/utils/patch";
//patching and added the manage recurring button
patch(ActivityMenu.prototype, {

     onClickCustomLink() {
        document.body.click();
        this.env.services.action.doAction({
             name: "Recurring Activities",
             type: 'ir.actions.act_window',
             res_model: 'recurring.activity',
             view_type: 'list',
             views: [[false, 'list'], [false, 'form']],
             target: 'current',
             context: {create: true}
        },
        {
            clearBreadcrumbs: true,
        });
     },
});
