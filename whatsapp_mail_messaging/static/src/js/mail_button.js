odoo.define('global_mail_message.mail_button', function(require) {
    "use strict";
    var SystrayMenu = require('web.SystrayMenu');
    var Widget = require('web.Widget');
    var ActionMenu = Widget.extend({
        template: 'global_mail_message.mail_icon',
        events: {
            'click .mail_icon': 'onclick_mail_icon',
        },
        onclick_mail_icon: function() {
            var self = this;
            self.do_action({
                name: 'Compose Mail',
                res_model: 'mail.compose.message',
                views: [[false, 'form']],
                type: 'ir.actions.act_window',
                view_mode: 'form',
                target: 'new'
            });
        },
    });
    SystrayMenu.Items.push(ActionMenu);
    return ActionMenu;
});