/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
const { Component } = owl;
/** @extends {Component<UserSwitchWidget>} for switching users */
export class UserSwitchWidget extends Component {
    setup() {
        super.setup();
        this.rpc = useService("rpc");
        this.action = useService("action");
    }
       async _onClick(){
        var result = await this.rpc("/switch/user", {});
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
                this.rpc("/switch/admin", {}).then(function(){
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
