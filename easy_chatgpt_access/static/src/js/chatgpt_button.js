/** @odoo-module */
import { registry } from "@web/core/registry";
import { Component } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { EasyChatGPTDialog } from "./EasyChatGPTDialog";

export class SystrayIcon extends Component {
    static template = "easy_chatgpt_access.SystrayIcon";

    setup() {
        this.dialogService = useService("dialog");
    }

    _onClick() {
        this.dialogService.add(EasyChatGPTDialog, {
            systray: {
                insert: false,
            },
        });
    }
}

export const systrayItem = {
    Component: SystrayIcon,
};

registry.category("systray").add("easy_chatgpt_access.SystrayIcon", systrayItem, { sequence: 50 });
