/** @odoo-module **/

/**
 * Dashboard Wrapper Component
 * Handles loading state and renders the Health Dashboard component.
 */

import { Component, useState, onMounted } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { HealthDashboard } from "./health_dashboard";

/**
 * Wrapper component for dashboard loading state.
 */
export class DashboardWrapper extends Component {
    setup() {
        this.state = useState({ dashboard_loading: true });
        onMounted(async () => {
            await new Promise((r) => setTimeout(r, 1));
            this.state.dashboard_loading = false;
        });
    }
    static components = { HealthDashboard };
    static template = "odoo_health_report.DashboardWrapper";
}
registry.category("actions").add("odoo_health_report.dashboard_wrapper", DashboardWrapper);
