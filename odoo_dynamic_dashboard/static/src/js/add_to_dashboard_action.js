/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component } from "@odoo/owl";

const cogMenuRegistry = registry.category("cogMenu");

export class AddToDashboardMenu extends Component {
    setup() {
        this.action = useService("action");
        this.notification = useService("notification");
    }

    async openWizard() {
        const controller = this.action.currentController;
        if (!controller) {
            return;
        }

        const props = controller.props;
        const resModel = props.resModel;
        const viewType = props.type;

        // Validation for Form View
        if (viewType === 'form') {
            this.notification.add("Cannot create dashboard card for form view", {
                title: "Action Not Allowed",
                type: "danger",
            });
            return;
        }

        if (!resModel) {
            this.notification.add("Model detection failed.", { type: "danger" });
            return;
        }

        // Handle Domain detection for both standard views and activity views
        let domain = props.domain || [];
        if (controller.searchModel && controller.searchModel.domain) {
            domain = controller.searchModel.domain;
        }

        await this.action.doAction({
            name: "Add to Dashboard",
            type: "ir.actions.act_window",
            res_model: "add.to.dashboard.wizard",
            view_mode: "form",
            views: [[false, "form"]],
            target: "new",
            context: {
                default_res_model: resModel,
                default_view_type: viewType,
                default_domain: JSON.stringify(domain),
                default_card_name: `${resModel.split('.').map(s => s.charAt(0).toUpperCase() + s.slice(1)).join(' ')} ${viewType === 'activity' ? 'Activities' : '(' + viewType + ')'}`,
            }
        });
    }
}

AddToDashboardMenu.template = "odoo_dynamic_dashboard.AddToDashboardMenu";

cogMenuRegistry.add("add-to-dashboard-menu", {
    Component: AddToDashboardMenu,
    groupNumber: 10,
});