odoo.define('vista_backend_theme.theme', function (require) {
    "use strict";

    var SystrayMenu = require('web.SystrayMenu');
    var Widget = require('web.Widget');
    var Session = require('web.session');

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
            var menu = $('.o_menu_sections');
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
    return ThemeWidget;
});
