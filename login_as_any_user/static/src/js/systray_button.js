/** @odoo-module **/
import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";

/** @extends {Component} for switching users */
export class UserSwitchWidget extends Component {
    static template = "login_as_any_user.UserSwitchSystray";

    setup() {
        this.action = useService("action");
        this._onClick = this._onClick.bind(this);
    }

    async _onClick() {
        const result = await rpc("/switch/user", {});
        if (result === true) {
            this.action.doAction({
                type: 'ir.actions.act_window',
                name: 'Switch User',
                res_model: 'user.selection',
                view_mode: 'form',
                views: [
                    [false, 'form'],
                ],
                target: 'new',
            });
        } else {
            await rpc("/switch/admin", {});
            location.reload();
        }
    }
}

export const systrayItem = {
    Component: UserSwitchWidget,
};

registry.category("systray").add("login_as_any_user.UserSwitchSystray", systrayItem, { sequence: 50 });

