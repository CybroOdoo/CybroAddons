/** @odoo-module **/

import SystrayMenu from 'web.SystrayMenu';
import Widget from 'web.Widget';
import Session from 'web.session';


var ThemeWidget = Widget.extend({
    template: 'theme_systray',
    events: {
        'click #theme_vista': '_onClick',
    },
    is_admin: false,
    willStart: function () {
            this.is_admin = Session.is_admin;
            return this._super.apply(this, arguments);
    },
    _onClick: function(){
        this.do_action({
             type: 'ir.actions.act_window',
             name: 'theme data',
             res_model: 'theme.data',
             view_mode: 'form',
             views: [[false, 'form']],
             target: 'new'
        });
    },
});
SystrayMenu.Items.push(ThemeWidget);
export default ThemeWidget;
