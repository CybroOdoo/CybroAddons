/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component } from "@odoo/owl";

export class ClientSupportSystray extends Component {
    /* Extending component and creating class ClientSupportSystray */
    setup() {
        this.action = useService("action");
    }
    async openSupport(){
    /*  Function for opening support wizard  */
        this.action.doAction({
            name: 'Support Form',
            type: 'ir.actions.act_window',
            res_model: 'client.support',
            view_mode: 'form',
            views: [[false, 'form']],
            target: "new",
        })
    }
}
ClientSupportSystray.template = "ClientSupportSystray";
export const systrayItem = { Component: ClientSupportSystray};
registry.category("systray").add("ClientSupportSystray", systrayItem);
