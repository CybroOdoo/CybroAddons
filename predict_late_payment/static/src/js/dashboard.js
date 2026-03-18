/** @odoo-module **/
/**
 * Payment Risk Dashboard – client-side enhancements.
 * Adds a summary banner above the kanban view showing aggregate KPIs.
 */
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onMounted, useState } from "@odoo/owl";

class PaymentRiskDashboardSummary extends Component {
    static template = "predict_late_payment.DashboardSummary";

    setup() {
        this.rpc = useService("rpc");
        this.state = useState({
            critical: 0, high: 0, medium: 0, low: 0,
            totalOverdue: 0, currency: "",
        });
        onMounted(() => this._loadSummary());
    }

    async _loadSummary() {
        try {
            const data = await this.rpc("/web/dataset/call_kw", {
                model: "payment.risk.score",
                method: "read_group",
                args: [[], ["risk_level", "total_overdue_amount:sum"], ["risk_level"]],
                kwargs: {},
            });
            let totals = { critical: 0, high: 0, medium: 0, low: 0, totalOverdue: 0 };
            data.forEach(group => {
                totals[group.risk_level] = group.risk_level_count;
                totals.totalOverdue += group.total_overdue_amount || 0;
            });
            Object.assign(this.state, totals);
        } catch (e) {
            // silently ignore
        }
    }
}
