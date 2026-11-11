/** @odoo-module **/

import { Component, proxy } from "@odoo/owl";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { useDropdownState } from "@web/core/dropdown/dropdown_hooks";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

/**
 * ScheduledActions component for managing scheduled actions in the systray.
 */
export class ScheduledActions extends Component {
    static template = "scheduled_action_shortcut.ScheduledActionSystray";
    static components = { Dropdown };

    setup() {
        this.dropdown = useDropdownState();
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.action = useService("action");
        this.state = proxy({
            actions: [],
            loading: false,
        });
    }

    async onBeforeOpen() {
        this.state.loading = true;
        try {
            const data = await this.orm.call("ir.cron", "search_read", [], {
                domain: [["run_through_systray", "=", true]],
                fields: ["cron_name", "nextcall"],
            });
            this.state.actions = data || [];
        } catch (error) {
            console.error("Error fetching scheduled actions:", error);
        } finally {
            this.state.loading = false;
        }
    }

    async runScheduledAction(cronId, cronName) {
        try {
            const result = await this.orm.call("ir.cron", "run_scheduled_actions", [cronId]);
            if (result !== true) {
                // The job failed: the server returns a display_exception action
                if (result && result.type) {
                    await this.action.doAction(result);
                }
                this.notification.add(
                    `Failed to execute scheduled action "${cronName || 'Action'}".`,
                    { type: "danger" }
                );
                return;
            }
            this.notification.add(
                `Scheduled action "${cronName || 'Action'}" executed successfully.`,
                { type: "success" }
            );
            await this.onBeforeOpen();
        } catch (error) {
            console.error("Error executing scheduled action:", error);
            this.notification.add(
                `Failed to execute scheduled action "${cronName || 'Action'}".`,
                { type: "danger" }
            );
        }
    }
}

export const systrayItem = {
    Component: ScheduledActions,
};

registry.category("systray").add("scheduled_action_shortcut.systray", systrayItem, {
    sequence: 22,
});
