/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState, onWillStart, onMounted, useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { loadJS } from "@web/core/assets";

class SentimentDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.doughnutCanvasRef = useRef("doughnutChart");
        this.charts = {};
        this.state = useState({
            high_risk: 0, medium_risk: 0, low_risk: 0, total: 0,
            avg_sentiment: 0, customers_at_risk: 0,
            positive_count: 0, neutral_count: 0, negative_count: 0,
            top_customers: [],
            loading: true,
        });

        onWillStart(async () => {
            await loadJS("/web/static/lib/Chart/Chart.js");
            await this.loadData();
        });

        onMounted(() => {
            this.renderCharts();
        });
    }

    async loadData() {
        this.state.loading = true;
        try {
            const [
                highRisk, mediumRisk, lowRisk, total, partnersAtRisk, sentimentData,
                positiveCount, neutralCount, negativeCount, topCustomers
            ] = await Promise.all([
                this.orm.searchCount("helpdesk.ticket", [["risk_level", "=", "high"], ["stage_id.fold", "=", false]]),
                this.orm.searchCount("helpdesk.ticket", [["risk_level", "=", "medium"], ["stage_id.fold", "=", false]]),
                this.orm.searchCount("helpdesk.ticket", [["risk_level", "=", "low"], ["stage_id.fold", "=", false]]),
                this.orm.searchCount("helpdesk.ticket", [["stage_id.fold", "=", false]]),
                this.orm.searchCount("res.partner", [["is_at_risk", "=", true]]),
                this.orm.readGroup("helpdesk.ticket", [["sentiment_score", "!=", false], ["stage_id.fold", "=", false]], ["sentiment_score:avg"], []),
                this.orm.searchCount("helpdesk.ticket", [["sentiment_score", ">=", 0.2], ["stage_id.fold", "=", false]]),
                this.orm.searchCount("helpdesk.ticket", [["sentiment_score", ">", -0.2], ["sentiment_score", "<", 0.2], ["stage_id.fold", "=", false]]),
                this.orm.searchCount("helpdesk.ticket", [["sentiment_score", "<=", -0.2], ["stage_id.fold", "=", false]]),
                this.orm.searchRead(
                    "res.partner",
                    ["|", ["is_at_risk", "=", true], ["customer_health_score", "<=", 55]],
                    ["name", "customer_health_score", "customer_health_label", "is_at_risk"],
                    { limit: 5, order: "customer_health_score asc" }
                )
            ]);

            this.state.high_risk = highRisk;
            this.state.medium_risk = mediumRisk;
            this.state.low_risk = lowRisk;
            this.state.total = total;
            this.state.customers_at_risk = partnersAtRisk;
            this.state.avg_sentiment = sentimentData.length && sentimentData[0]["sentiment_score"]
                ? parseFloat(sentimentData[0]["sentiment_score"]).toFixed(2) : 0;
            this.state.positive_count = positiveCount;
            this.state.neutral_count = neutralCount;
            this.state.negative_count = negativeCount;

            this.state.top_customers = topCustomers.map(partner => {
                let score = partner.customer_health_score || 0;
                if (score <= 35) {
                    partner.badge_class = "bg-danger text-white";
                } else if (score <= 55) {
                    partner.badge_class = "bg-warning-subtle text-warning-emphasis border border-warning border-opacity-25";
                } else if (score <= 75) {
                    partner.badge_class = "bg-light text-secondary border";
                } else {
                    partner.badge_class = "bg-success text-white";
                }
                return partner;
            });

            if (this.charts.doughnut) {
                this.renderCharts();
            }

        } catch (error) {
            console.error("Dashboard load error:", error);
        }
        this.state.loading = false;
    }

    renderCharts() {
        if (!window.Chart) return;
        if (this.charts.doughnut) this.charts.doughnut.destroy();

        if (this.doughnutCanvasRef.el) {
            let chartData = [this.state.positive_count, this.state.neutral_count, this.state.negative_count];
            let bgColors = ['#198754', '#dee2e6', '#dc3545'];
            let labels = ['Positive', 'Neutral', 'Negative'];

            if (this.state.total > 0 && (this.state.positive_count + this.state.neutral_count + this.state.negative_count) === 0) {
                chartData = [this.state.total]; bgColors = ['#e9ecef']; labels = ['Unscored'];
            } else if (this.state.total === 0) {
                chartData = [1]; bgColors = ['#f8f9fa']; labels = ['No Data'];
            }

            this.charts.doughnut = new Chart(this.doughnutCanvasRef.el, {
                type: 'doughnut', data: { labels: labels, datasets: [{ data: chartData, backgroundColor: bgColors, borderWidth: 0 }] },
                options: { responsive: true, maintainAspectRatio: false, cutout: '75%', plugins: { legend: { display: false } } }
            });
        }
    }

    openHighRisk() { this._openTicketView([["risk_level", "=", "high"], ["stage_id.fold", "=", false]], "Open Critical Tickets"); }
    openMediumRisk() { this._openTicketView([["risk_level", "=", "medium"], ["stage_id.fold", "=", false]], "Open Attention Needed"); }
    openAllTickets() { this._openTicketView([["stage_id.fold", "=", false]], "All Open Tickets"); }

    openCustomersAtRisk() { this.action.doAction({ type: "ir.actions.act_window", name: "Customers At Risk", res_model: "res.partner", views: [[false, "list"], [false, "form"]], domain: [["is_at_risk", "=", true]] }); }
    openPartner(id) { this.action.doAction({ type: "ir.actions.act_window", res_model: "res.partner", res_id: id, views: [[false, "form"]] }); }
    _openTicketView(domain, name) { this.action.doAction({ type: "ir.actions.act_window", name: name, res_model: "helpdesk.ticket", views: [[false, "list"], [false, "form"]], domain: domain }); }
}

SentimentDashboard.template = "customer_success_sentiment_tracker.Dashboard";
registry.category("actions").add("action_sentiments_dashboard", SentimentDashboard);
