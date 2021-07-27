odoo.define('code_backend_theme.SideBar', function (require) {
    "use strict";

    var Widget = require('web.Widget');
    var SideBar = Widget.extend({
        events: _.extend({}, Widget.prototype.events, {
            'click .nav-link': '_onAppsMenuItemClicked',
        }),
        template: "code_backend_theme.Sidebar",

        init: function (parent, menuData) {
            this._super.apply(this, arguments);
            this._apps = _.map(menuData.children, function (appMenuData) {
                return {
                    actionID: parseInt(appMenuData.action.split(',')[1]),
                    menuID: appMenuData.id,
                    name: appMenuData.name,
                    xmlID: appMenuData.xmlid,
                    web_icon_data: appMenuData.web_icon_data,
                };
            });
        },

        getApps: function () {
            return this._apps;
        },

        _openApp: function (app) {
            this.trigger_up('app_clicked', {
                action_id: app.actionID,
                menu_id: app.menuID,
            });
        },

        _onAppsMenuItemClicked: function (ev) {
            var $target = $(ev.currentTarget);
            var actionID = $target.data('action-id');
            var menuID = $target.data('menu-id');
            var app = _.findWhere(this._apps, { actionID: actionID, menuID: menuID });
            this._openApp(app);
        },
    });
    return SideBar;
});