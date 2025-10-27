/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
const { Component } = owl;
import { rpc } from "@web/core/network/rpc";
/** @extends {Component<UserSwitchWidget>} for switching users */
export class UserSwitchWidget extends Component {
    setup() {
        super.setup();
        this.action = useService("action");
    }
       async _onClick(){
        var result = await rpc("/switch/user", {});
            if (result == true) {
                this.action.doAction({
                    type: 'ir.actions.act_window',
                    name: 'Switch User',
                    res_model: 'user.selection',
                    view_mode: 'form',
                    views: [
                        [false, 'form']
                    ],
                    target: 'new'
                })
            }else{
                rpc("/switch/admin", {}).then(function(){
                    location.reload();
                })
            }
      }
}
UserSwitchWidget.template = "UserSwitchSystray";
const Systray = {
    Component: UserSwitchWidget
}
registry.category("systray").add("UserSwitchSystray", Systray)
