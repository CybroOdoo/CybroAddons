/** @odoo-module **/
import { ActionContainer } from "@web/webclient/actions/action_container"
import { patch } from "@web/core/utils/patch";
var ajax = require("web.ajax");
/** Patching the action container for updating the color of highlight **/
patch(ActionContainer.prototype, "field_highlight", {
/** To set up the styles of fields**/
    setup() {
        this.info = {};
        this.info = {};
        this.env.bus.on("ACTION_MANAGER:UPDATE", this, (info) => {
            this.info = info;
            this.render();
            var list=[]
            ajax.jsonRpc('/mandatory/config_params', 'call', {
            }).then(function (data) {
                for (let x in data) {
                    list.push(data[x]);
                }
                 const root = document.documentElement;
                /**Setting all the style properties**/
                 root.style.setProperty('--background-color',list[4]);
                 root.style.setProperty('--margin-left-color',list[0]);
                 root.style.setProperty('--margin-right-color',list[1]);
                 root.style.setProperty('--margin-top-color',list[2]);
                 root.style.setProperty('--margin-bottom-color',list[3]);
            });
        });
    }
});
