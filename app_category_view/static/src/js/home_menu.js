/**@odoo-module**/
import { patch } from "@web/core/utils/patch";
import { url } from "@web/core/utils/urls";
import { HomeMenu } from "@web_enterprise/webclient/home_menu/home_menu"
const { onMounted } = owl;
var rpc = require('web.rpc');
patch(HomeMenu.prototype, "home_menu.AppCategory", {
    async setup() {
        this._super(...arguments);
        const self = this;
        await rpc.query({
            model: "ir.app.category",
            method: "get_home_dashboard",
            args: []
        }).then(function(data) {
            self.appCategory = data;
            self.render();
        });
        await rpc.query({
            model: "ir.app.category",
            method: "get_other_apps",
            args: []
        }).then(function(otherApps) {
            self.otherApps = otherApps;
            self.render();
        });
    },
});
