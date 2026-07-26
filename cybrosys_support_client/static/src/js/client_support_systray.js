/** @odoo-module **/

import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { useHotkey } from "@web/core/hotkeys/hotkey_hook";

export class ClientSupportSystray extends Component {
    static template = "cybrosys_support_client.ClientSupportSystray";
    static props = {};

    setup() {
        this.actionService = useService("action");
        useHotkey("alt+shift+h", () => this.openSupport(), { global: true });
    }

    async openSupport() {
        return this.actionService.doAction({
            name: "Cybrosys Support",
            type: "ir.actions.act_window",
            res_model: "client.support",
            view_mode: "form",
            views: [[false, "form"]],
            target: "new",
        });
    }
}

registry.category("systray").add(
    "cybrosys_support_client.ClientSupportSystray",
    { Component: ClientSupportSystray },
    { sequence: 100 }
);
