/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onMounted, useEffect } from "@odoo/owl";
import { user } from "@web/core/user";


export class ScheduledActions extends Component {
    static template = "all_in_one_announcementsSystray";

    setup() {
        this.action = useService("action");
        this.orm = useService("orm");
        this.state = useState({
            task_details: [],
            purchase_details: [],
            sale_details: [],
            crm_details: [],
            display_dropdown: false,
            has_manager_group: false,
        });

        onMounted(async () => {
            await this.checkGrp();
            document.addEventListener("click", this.onBodyClick.bind(this));
        });
    }

    async checkGrp() {
        const hasGroup = await user.hasGroup(
            "all_in_one_announcements.announcement_group_manager"
        );
        this.state.has_manager_group = hasGroup;
        return hasGroup;
    }

    async _onClick() {
        if (!this.state.has_manager_group) return;

        const res = await this.orm.call("project.task", "task_assigned");
        this.state.task_details = res[0] || [];
        this.state.purchase_details = res[1] || [];
        this.state.sale_details = res[2] || [];
        this.state.crm_details = res[3] || [];

        this.state.display_dropdown = !this.state.display_dropdown;
    }

    onBodyClick(ev) {
        if (this.state.display_dropdown && !ev.target.closest(".list_headers") && !ev.target.closest("#announcement_div")) {
            this.state.display_dropdown = false;
        }
    }

    async openTaskView(ev) {
        const modelId = ev.currentTarget.getAttribute("data-model");
        const id = ev.currentTarget.getAttribute("data-id");
        const result = await this.orm.call(modelId, "get_pending_tasks", [id]);
        this.action.doAction(result);
    }
}

export const systrayItem = {
    Component: ScheduledActions,
};

registry.category("systray").add("all_in_one_announcements.ScheduledActions", systrayItem, {
    sequence: 1,
});
