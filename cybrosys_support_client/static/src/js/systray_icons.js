/** @odoo-module **/
import core from 'web.core';
import SystrayMenu from 'web.SystrayMenu';
import Widget from 'web.Widget';
var QWeb = core.qweb;

var ClientSupportSystray = Widget.extend({
    template: 'ClientSupportSystray',
    events: {
       'click #support': 'openSupport',
   },
    openSupport :function(){
        this.do_action({
            name: 'Support Form',
            type: 'ir.actions.act_window',
            res_model: 'client.support',
            view_mode: 'form',
            views: [[false, 'form']],
            target: "new",
        })
    }
});
SystrayMenu.Items.push(ClientSupportSystray);
export default ClientSupportSystray;
