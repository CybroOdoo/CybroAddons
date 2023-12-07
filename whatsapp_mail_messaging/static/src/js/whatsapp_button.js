/** @odoo-module **/
console.log('wht')
import SystrayMenu from 'web.SystrayMenu';
import Widget from 'web.Widget';

const { Component } = owl;

var ActionMenu = Widget.extend({
    template: 'whatsapp_mail_messaging.whatsapp_icon',
    events: {
        'click .whatsapp_icon': 'onclick_whatsapp_icon',
    },
    onclick_whatsapp_icon: function() {
        var self = this;
        console.log(this,"TEST")
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

export default ActionMenu;
