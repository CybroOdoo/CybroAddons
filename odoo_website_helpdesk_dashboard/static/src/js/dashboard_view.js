import { Component, onWillStart, proxy, useProps } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { useChart } from "@web/core/utils/chart_hook";
import { useService } from "@web/core/utils/hooks";
import { standardActionServiceProps } from "@web/webclient/actions/action_plugin";

const STATUS_COLORS = ["#665191", "#ff7c43", "#ffa600"];
const TEAM_COLORS = ["#ff6384", "#ff9f40", "#ffcd56", "#4bc0c0", "#36a2eb", "#9966ff", "#c9cbcf"];

/**
 * HelpDesk dashboard: ticket counters, ticket priorities, customer reviews,
 * a chart of the ticket status, a chart of the tickets per team and the
 * latest tickets
 */
export class HelpDeskDashBoard extends Component {
    static template = "odoo_website_helpdesk_dashboard.HelpDeskDashBoard";
    props = useProps(standardActionServiceProps);

    statusChart = useChart(() => this.getStatusChartConfig());
    teamChart = useChart(() => this.getTeamChartConfig());

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = proxy({ data: null });
        onWillStart(() => this.loadData());
    }

    async loadData() {
        this.state.data = await this.orm.call("ticket.helpdesk", "get_dashboard_data", []);
    }

    get cards() {
        const counts = this.state.data.counts;
        return [
            { key: "new", label: _t("New Tickets"), icon: "inbox", count: counts.new },
            {
                key: "in_progress",
                label: _t("Tickets In Progress"),
                icon: "hourglass_top",
                count: counts.in_progress,
            },
            { key: "done", label: _t("Done Tickets"), icon: "check_circle", count: counts.done },
            {
                key: "teams",
                label: _t("HelpDesk Teams"),
                icon: "group",
                count: this.state.data.team_count,
            },
        ];
    }

    getStatusChartConfig() {
        const counts = this.state.data.counts;
        return {
            type: "doughnut",
            data: {
                labels: [_t("New"), _t("In Progress"), _t("Done")],
                datasets: [
                    {
                        data: [counts.new, counts.in_progress, counts.done],
                        backgroundColor: STATUS_COLORS,
                    },
                ],
            },
            options: {
                maintainAspectRatio: false,
                plugins: { legend: { position: "right" } },
            },
        };
    }

    getTeamChartConfig() {
        const teamChart = this.state.data.team_chart;
        return {
            type: "bar",
            data: {
                labels: teamChart.labels,
                datasets: [
                    {
                        label: _t("Tickets"),
                        data: teamChart.values,
                        backgroundColor: TEAM_COLORS,
                        borderRadius: 6,
                    },
                ],
            },
            options: {
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
            },
        };
    }

    /** Open the tickets of a card, or the helpdesk teams */
    openCard(card) {
        if (card.key === "teams") {
            return this.action.doAction({
                name: _t("HelpDesk Teams"),
                type: "ir.actions.act_window",
                res_model: "team.helpdesk",
                views: [
                    [false, "list"],
                    [false, "form"],
                ],
            });
        }
        return this.action.doAction({
            name: card.label,
            type: "ir.actions.act_window",
            res_model: "ticket.helpdesk",
            views: [
                [false, "list"],
                [false, "form"],
            ],
            domain: [["stage_id", "in", this.state.data.stage_ids[card.key]]],
        });
    }

    /** Open one of the latest tickets */
    openTicket(ticket) {
        return this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "ticket.helpdesk",
            res_id: ticket.id,
            views: [[false, "form"]],
        });
    }
}

registry.category("actions").add("helpdesk_dashboard", HelpDeskDashBoard);
