odoo.define('dodger_blue.sidebar', function (require) {
    'use strict';

    var AppsMenu = require("web.AppsMenu");
    var core = require('web.core');
    var QWeb = core.qweb;
    var session = require('web.session');

    AppsMenu.include({
        init: function (parent, menuData) {
            this.user_id = session.uid;
            this.session = session;
            this._super.apply(this, arguments);
            console.log(this._apps[0].web_icon_data,"this")
            var sidebar = QWeb.render('AppsMenuSidebar',{
                widget:this
            });
            $('.cybro-sidebar').html(sidebar);
        }
    });
});
