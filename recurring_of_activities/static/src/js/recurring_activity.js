/** @odoo-module **/

import ActivityMenu from '@mail/js/systray/systray_activity_menu';

ActivityMenu.include({
    events: _.extend({}, ActivityMenu.prototype.events, {
        'click .o_custom_link': 'onClickCustomLink',
    }),
    onClickCustomLink(ev) {
         this.do_action({
             name: "Recurring Activities",
             type: 'ir.actions.act_window',
             res_model: 'recurring.activity',
             view_type: 'list',
             views: [[false, 'list'], [false, 'form']],
             target: 'current',
             context: {create: true}
         });
    },
});
