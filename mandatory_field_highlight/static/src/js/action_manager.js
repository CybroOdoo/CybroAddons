/** @odoo-module **/
import { ActionContainer } from "@web/webclient/actions/action_container"
import { Component, xml, onWillDestroy } from "@odoo/owl";
import { patch } from "@web/core/utils/patch";

//Patching the action container for showing the menu_lock wizard
patch(ActionContainer.prototype, {
    setup() {
        this.info = {};
        //Updating the action manager
        this.onActionManagerUpdate = async ({ detail: info }) => {
            this.info = info;
            this.render();
            var list=[]
             const rpc = this.env.services.rpc
        const data = await rpc('/mandatory/config_params')
         for (let x in data) {
                list.push(data[x]);
                }
                 const root = document.documentElement;
                //Setting all the style properties
                 root.style.setProperty('--background-color',list[4]);
                 root.style.setProperty('--margin-left-color',list[0]);
                 root.style.setProperty('--margin-right-color',list[1]);
                 root.style.setProperty('--margin-top-color',list[2]);
                 root.style.setProperty('--margin-bottom-color',list[3]);
        };
        this.env.bus.addEventListener("ACTION_MANAGER:UPDATE",
        this.onActionManagerUpdate);
        onWillDestroy(() => {
            this.env.bus.removeEventListener("ACTION_MANAGER:UPDATE",
            this.onActionManagerUpdate);
        });
    }
});
