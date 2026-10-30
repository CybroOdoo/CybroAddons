import { registry } from "@web/core/registry";
import { Component, signal } from "@odoo/owl";
import { onWillStart, onMounted, onWillUnmount, proxy } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { browser } from "@web/core/browser/browser";
import { cookie } from "@web/core/browser/cookie";

const THEME_STORAGE_KEY = "crm_dashboard.theme";

const PERIODS = [
    { value: "year", label: "This Year" },
    { value: "quarter", label: "This Quarter" },
    { value: "month", label: "This Month" },
    { value: "week", label: "This Week" },
];

const CHART_THEMES = {
    light: {
        text: "#475569",
        grid: "rgba(15, 23, 42, 0.08)",
        surface: "#ffffff",
        palette: ["#003f5c", "#2f4b7c", "#f95d6a", "#665191", "#d45087", "#ff7c43", "#ffa600", "#a05195", "#6d5c16"],
    },
    dark: {
        text: "#cbd5e1",
        grid: "rgba(148, 163, 184, 0.18)",
        surface: "#1e293b",
        palette: ["#4f9dc9", "#7b93d8", "#f95d6a", "#9d87d9", "#e0679e", "#ff8f5e", "#ffb733", "#c475bc", "#b9a23f"],
    },
};

export class CrmDashboard extends Component {

    // Odoo 20 DOM refs (class fields using signal.ref(), accessed as this.RefName())
    Leadstage = signal.ref();
    LeadByMonth = signal.ref();
    CrmActivities = signal.ref();
    LeadByCampaign = signal.ref();
    LeadByMedium = signal.ref();
    LeadBySource = signal.ref();
    LostLead = signal.ref();
    TotalRevenue = signal.ref();

    setup() {
        super.setup(...arguments);
        this.orm = useService("orm");
        this.action = useService("action");

        this.periods = PERIODS;
        // Chart.js instances must stay out of the reactive state: a proxied
        // chart is never removed from Chart.js' animator when destroyed
        this.charts = [];
        this.state = proxy({
            period: 'month',
            darkMode: this._getInitialDarkMode(),
            leads: null,
            opportunities: null,
            exp_revenue: null,
            revenue: null,
            win_ratio: null,
            avg_close_time: null,
            opportunity_ratio: null,
            unassigned_leads: null,
            upcoming_events: [],
            top_sp_revenue: [],
            country_count: [],
            country_revenue: [],
            recent_activities: [],
        });

        onWillStart(async () => {
            await this.fetch_data();
            await this.UpcomingEvents();
            await this.TopSpRevenue();
            await this.TopCountryRevenue();
            await this.TopCountryCount();
            await this.RecentActivities();
        });

        onMounted(async () => {
            await this._renderAllCharts();
        });

        onWillUnmount(() => this._destroyCharts());


    }

    _destroyCharts() {
        this.charts.forEach(chart => chart.destroy());
        this.charts = [];
    }

    async _renderAllCharts() {
        await this.render_leads_by_stage();
        await this.render_leads_by_month();
        await this.render_crm_activities();
        await this.render_lead_by_campaign();
        await this.render_lead_by_medium();
        await this.render_lead_by_source();
        await this.render_lost_lead();
        await this.render_total_revenue();
    }

    async fetch_data() {
        const result = await this.orm.call('crm.lead', "get_data", [this.state.period]);
        this.state.leads = result['leads'];
        this.state.opportunities = result['opportunities'];
        this.state.exp_revenue = result['exp_revenue'];
        this.state.revenue = result['revenue'];
        this.state.win_ratio = result['win_ratio'];
        this.state.opportunity_ratio = result['opportunity_ratio'];
        this.state.avg_close_time = result['avg_close_time'];
        this.state.unassigned_leads = result['unassigned_leads'];
    }

    async UpcomingEvents() {
        const result = await this.orm.call('crm.lead', "get_upcoming_events", []);
        this.state.upcoming_events = result['event'];
    }

    async TopSpRevenue() {
        const result = await this.orm.call('crm.lead', "get_top_sp_revenue", [this.state.period]);
        this.state.top_sp_revenue = result['top_revenue'];
    }

    async TopCountryCount() {
        const result = await this.orm.call('crm.lead', "get_top_country_count", [this.state.period]);
        this.state.country_count = result['country_count'];
    }

    async TopCountryRevenue() {
        const result = await this.orm.call('crm.lead', "get_top_country_revenue", [this.state.period]);
        this.state.country_revenue = result['country_revenue'];
    }

    async RecentActivities() {
        const result = await this.orm.call('crm.lead', "get_recent_activities", []);
        this.state.recent_activities = result['activities'];
    }

    get periodLabel() {
        return PERIODS.find((period) => period.value === this.state.period).label;
    }

    get periodStartLabel() {
        return this._getPeriodStartDate().toLocaleDateString(undefined, {
            day: "numeric",
            month: "short",
            year: "numeric",
        });
    }

    _getPeriodStartDate() {
        const today = new Date();
        if (this.state.period === 'year') {
            return new Date(today.getFullYear(), 0, 1);
        } else if (this.state.period === 'quarter') {
            const startMonth = Math.floor(today.getMonth() / 3) * 3;
            return new Date(today.getFullYear(), startMonth, 1);
        } else if (this.state.period === 'week') {
            const dayOfWeek = today.getDay();
            const diff = today.getDate() - dayOfWeek + (dayOfWeek === 0 ? -6 : 1);
            return new Date(today.getFullYear(), today.getMonth(), diff);
        }
        return new Date(today.getFullYear(), today.getMonth(), 1);
    }

    SetPeriods() {
        const start_date = this._getPeriodStartDate();
        return start_date.getFullYear() + '-' + (start_date.getMonth() + 1).toString().padStart(2, '0') + '-' + start_date.getDate().toString().padStart(2, '0');
    }

    async setPeriod(period) {
        if (period === this.state.period) {
            return;
        }
        this.state.period = period;
        await this._reloadPeriodData();
    }

    async _reloadPeriodData() {
        this._destroyCharts();
        await this.fetch_data();
        await this.TopSpRevenue();
        await this.TopCountryRevenue();
        await this.TopCountryCount();
        await this._renderAllCharts();
    }

    async onClickRefresh() {
        await this.UpcomingEvents();
        await this.RecentActivities();
        await this._reloadPeriodData();
    }

    _getInitialDarkMode() {
        try {
            const savedTheme = browser.localStorage.getItem(THEME_STORAGE_KEY);
            if (savedTheme) {
                return savedTheme === "dark";
            }
        } catch {
            // Storage can be unavailable (private mode); fall back to Odoo's scheme
        }
        return cookie.get("color_scheme") === "dark";
    }

    async toggleTheme() {
        this.state.darkMode = !this.state.darkMode;
        try {
            browser.localStorage.setItem(THEME_STORAGE_KEY, this.state.darkMode ? "dark" : "light");
        } catch {
            // The choice then only lasts for the current page
        }
        this._destroyCharts();
        await this._renderAllCharts();
    }

    onClickLeads() {
        const date = this.SetPeriods();
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Leads",
            res_model: 'crm.lead',
            views: [[false, "kanban"], [false, "form"]],
            target: "current",
            domain: [['type', '=', 'lead'], ['create_date', '>=', date]]
        });
    }

    onClickOpportunities() {
        const date = this.SetPeriods();
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Opportunities",
            res_model: 'crm.lead',
            views: [[false, "kanban"], [false, "form"]],
            target: "current",
            domain: [['type', '=', 'opportunity'], ['create_date', '>=', date]]
        });
    }

    onClickExpRevenue() {
        const date = this.SetPeriods();
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Expected Revenue",
            res_model: 'crm.lead',
            views: [[false, "list"], [false, "form"]],
            target: "current",
            domain: [['type', '=', 'opportunity'], ['active', '=', true], ['create_date', '>=', date]]
        });
    }

    onClickRevenue() {
        const date = this.SetPeriods();
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Revenue",
            res_model: 'crm.lead',
            views: [[false, "list"], [false, "form"]],
            target: "current",
            domain: [['type', '=', 'opportunity'], ['active', '=', true], ['stage_id.is_won', '=', true], ['create_date', '>=', date]]
        });
    }

    onClickUnAssignedLeads() {
        const date = this.SetPeriods();
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Unassigned Leads",
            res_model: 'crm.lead',
            views: [[false, "list"], [false, "form"]],
            target: "current",
            domain: [['user_id', '=', false], ['type', '=', 'lead'], ['create_date', '>=', date]]
        });
    }

    _makeChart(canvas, type, data) {
        const Chart = window.Chart;
        if (!canvas || !Chart) return null;
        // A reload started before the previous one finished may have
        // already drawn on this canvas
        const existing = Chart.getChart(canvas);
        if (existing) {
            existing.destroy();
            this.charts = this.charts.filter((chart) => chart !== existing);
        }
        const theme = CHART_THEMES[this.state.darkMode ? "dark" : "light"];
        for (const dataset of data.datasets) {
            dataset.backgroundColor = theme.palette;
            dataset.borderColor = theme.surface;
        }
        const options = {
            color: theme.text,
            borderColor: theme.grid,
            plugins: { legend: { labels: { color: theme.text } } },
        };
        if (type === 'bar') {
            options.scales = {
                x: { ticks: { color: theme.text }, grid: { color: theme.grid } },
                y: { ticks: { color: theme.text }, grid: { color: theme.grid } },
            };
        } else if (type === 'polarArea') {
            options.scales = {
                r: {
                    ticks: { display: false },
                    grid: { color: theme.grid },
                    angleLines: { color: theme.grid },
                },
            };
        }
        return new Chart(canvas, { type, data, options });
    }

    async render_leads_by_stage() {
        const arrays = await this.orm.call('crm.lead', "get_lead_stage_data", [this.state.period]);
        const chart = this._makeChart(this.Leadstage(), 'polarArea', {
            labels: arrays[1],
            datasets: [{ label: 'Leads', data: arrays[0] }]
        });
        if (chart) this.charts.push(chart);
    }

    async render_leads_by_month() {
        const arrays = await this.orm.call('crm.lead', "get_lead_by_month", []);
        const chart = this._makeChart(this.LeadByMonth(), 'doughnut', {
            labels: arrays[1],
            datasets: [{ label: 'Leads', data: arrays[0] }]
        });
        if (chart) this.charts.push(chart);
    }

    async render_crm_activities() {
        const arrays = await this.orm.call('crm.lead', "get_crm_activities", [this.state.period]);
        const chart = this._makeChart(this.CrmActivities(), 'pie', {
            labels: arrays[1],
            datasets: [{ label: 'Activity', data: arrays[0] }]
        });
        if (chart) this.charts.push(chart);
    }

    async render_lead_by_campaign() {
        const arrays = await this.orm.call('crm.lead', "get_the_campaign_pie", [this.state.period]);
        const chart = this._makeChart(this.LeadByCampaign(), 'pie', {
            labels: arrays[1],
            datasets: [{ label: 'Activity', data: arrays[0] }]
        });
        if (chart) this.charts.push(chart);
    }

    async render_lead_by_medium() {
        const arrays = await this.orm.call('crm.lead', "get_the_medium_pie", [this.state.period]);
        const chart = this._makeChart(this.LeadByMedium(), 'pie', {
            labels: arrays[1],
            datasets: [{ label: 'Activity', data: arrays[0] }]
        });
        if (chart) this.charts.push(chart);
    }

    async render_lead_by_source() {
        const arrays = await this.orm.call('crm.lead', "get_the_source_pie", [this.state.period]);
        const chart = this._makeChart(this.LeadBySource(), 'pie', {
            labels: arrays[1],
            datasets: [{ label: 'Activity', data: arrays[0] }]
        });
        if (chart) this.charts.push(chart);
    }

    async render_lost_lead() {
        const arrays = await this.orm.call('crm.lead', "get_total_lost_crm", [this.state.period]);
        const chart = this._makeChart(this.LostLead(), 'bar', {
            labels: arrays['month'],
            datasets: [{ label: 'Lost', data: arrays['count'] }]
        });
        if (chart) this.charts.push(chart);
    }

    async render_total_revenue() {
        const arrays = await this.orm.call('crm.lead', "total_revenue_by_sales", [this.state.period]);
        const chart = this._makeChart(this.TotalRevenue(), 'pie', {
            labels: arrays[1],
            datasets: [{ label: 'Activity', data: arrays[0] }]
        });
        if (chart) this.charts.push(chart);
    }
}

CrmDashboard.template = 'CrmDashboard';
registry.category("actions").add("crm_dashboard", CrmDashboard);
