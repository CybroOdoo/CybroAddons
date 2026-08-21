/** @odoo-module **/

import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useHotkey } from "@web/core/hotkeys/hotkey_hook";
import { useService } from "@web/core/utils/hooks";

export class AutoDatabaseBackupSystray extends Component {
    static template = "auto_database_backup.AutoDatabaseBackupSystray";
    static props = {};

    setup() {
        this.actionService = useService("action");
        useHotkey("alt+shift+b", () => this.openDatabaseBackup(), { global: true });
    }

    async openDatabaseBackup() {
        return this.actionService.doAction({
            name: "Automatic Database Backup Support",
            type: "ir.actions.act_window",
            res_model: "auto.database.backup.support",
            view_mode: "form",
            views: [[false, "form"]],
            target: "new",
        });
    }
}

registry.category("systray").add(
    "auto_database_backup.AutoDatabaseBackupSystray",
    { Component: AutoDatabaseBackupSystray },
    { sequence: 100 }
);
