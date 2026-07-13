/** @odoo-module **/
import { registry } from '@web/core/registry';
import { _t } from "@web/core/l10n/translation";
import { AdvancedDashboardMenuCard } from "./dashboard_menu_card"
import { Component, onWillStart, useState, useRef, onMounted } from '@odoo/owl';
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { useService } from '@web/core/utils/hooks';
import { user } from "@web/core/user";
class AdvancedDashboard extends Component {
    setup() {
        this.action = useService("action");
        this.orm = useService('orm');
        this.dialogService = useService("dialog");
        this.state = useState({
            allDashboards: []
        });
        onWillStart(async () => {
            this.state.allDashboards = await this.orm.searchRead('dashboard.menu', [], []);
        });
    }
    async OnclickEditDashboard(dashboard_id) {
        await this.action.doAction({
            type: "ir.actions.act_window",
            name: "Edit Dashboard",
            res_model: "dashboard.menu",
            res_id: dashboard_id,
            views: [[false, "form"]],
            target: "new",
            context: {
                form_view_ref: "odoo_dynamic_dashboard.dashboard_menu_view_form_wizard",
            },
        },
            {
                onClose: async () => {
                    this.action.doAction("soft_reload")
                },
            })
    }
    async OnclickDeleteDashboard(dashboard_id, menu_id) {
        this.dialogService.add(ConfirmationDialog, {
            title: _t("Confirmation"),
            body: _t("Are you sure you want to delete this dashboard?"),
            confirm: async () => {
                await this.orm.unlink("ir.ui.menu", [parseInt(menu_id[0])]);
                await this.orm.unlink("dashboard.menu", [parseInt(dashboard_id)]);
                this.action.doAction("soft_reload")
            },
            cancel: () => { },
        });
    }
    async OnclickOpenDashboard(dashboard) {
        this.action.doAction({
            type: 'ir.actions.client',
            tag: 'DynamicDashboard',
            params: {
                dashboard_menu_id: dashboard,
            }
        });
    }
    async OnclickCreateDashboard() {
        await this.action.doAction({
            type: "ir.actions.act_window",
            name: "Create Dashboard Menu",
            res_model: "dashboard.menu",
            views: [[false, "form"]],
            target: "new",
            context: {
                form_view_ref: "odoo_dynamic_dashboard.dashboard_menu_view_form_wizard",
            },
        },
            {
                onClose: async () => {
                    this.action.doAction("soft_reload")
                },
            })
    }
}
AdvancedDashboard.template = 'AdvancedDashboardTemplate';
AdvancedDashboard.components = { AdvancedDashboardMenuCard };
registry.category('actions').add('AdvancedDashboard', AdvancedDashboard);
