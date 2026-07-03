/** @odoo-module **/

/**
 * Health Dashboard Component
 * Handles module selection and generates module health reports.
 */

import { Component, useState, onMounted } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { registry } from "@web/core/registry";
import { ModuleQuality } from "./module_quality";

/**
 * HealthDashboard Component
 */
export class HealthDashboard extends Component {
    static components = { ModuleQuality };

    setup() {
        const lastComponent = localStorage.getItem("activeComponent");
        const activeId = lastComponent ? parseInt(lastComponent) : 3;
        this.orm = useService('orm');
        this.action = useService('action');
        this.notification = useService('notification');

        this.state = useState({
            activeComponent: activeId,
            activeMenu: activeId,
            loading: false,
            module: false,
            module_selected: {},
            module_selected_desc: {},
            showOptions: false,
            select_module: [],
            value: [],
            checked_module: '',
        });

        onMounted(async () => {
            this.state.select_module = await this.orm.searchRead("ir.module.module", [['state', '=', 'installed'],
            ['name', '!=', 'odoo_health_report']]);
        });

        this.setActiveComponent = async (id) => {
            this.state.loading = true;
            this.state.activeMenu = id;

            localStorage.setItem("activeComponent", id);
            await new Promise((resolve) => setTimeout(resolve, 100))

            this.state.activeComponent = id;
            this.state.loading = false;
        };
    }

    exitDashboard() {
        window.location.href = window.location.origin + '/web';
    }

    onModuleSelectDesc(ev) {
        ev.stopPropagation()
        let module = ev.target.dataset.modName
        this.state.module_selected[module] = false
        delete this.state.module_selected_desc[module]
    }

    onModuleSelect(event) {
        const checked = event.target.checked;
        const moduleName = event.target.dataset.modName;
        const moduleShortdesc = event.target.dataset.modShortdesc;
        this.state.module_selected[moduleName] = checked;
        this.state.module_selected_desc[moduleName] = moduleShortdesc;
        if (checked == false) { delete this.state.module_selected_desc[moduleName] }
    }

    async onGenerateReport() {
        const selected = [];
        if (this.state.module) selected.push("module");

        const validOptions = ['module'];
        const hasValidOption = validOptions.some(opt => selected.includes(opt));
        if (!hasValidOption) {
            this.notification.add("Please select at least one option", { type: 'danger' });
            return;
        }

        const data = {
            selected,
            module_quality: this.state.module,
            module_selected: this.state.module_selected,
        };

        await this.action.doAction("odoo_health_report.action_odoo_health_report", {
            additionalContext: { data }
        })
    }
}
HealthDashboard.template = "odoo_health_report.health_dashboard";
registry.category("actions").add("health_dashboard_tag", HealthDashboard);
