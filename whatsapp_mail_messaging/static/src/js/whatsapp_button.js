odoo.define('whatsapp_mail_messaging.whatsapp_button', function(require) {
    "use strict";
    var SystrayMenu = require('web.SystrayMenu');
    var Widget = require('web.Widget');
    var ActionMenu = Widget.extend({
        template: 'whatsapp_mail_messaging.whatsapp_icon',
        events: {
            'click .whatsapp_icon': 'onclick_whatsapp_icon',
        },
        onclick_whatsapp_icon: function() {
            var self = this;
            self.do_action({
                name: 'Compose Whatsapp Message',
                res_model: 'whatsapp.message.wizard',
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