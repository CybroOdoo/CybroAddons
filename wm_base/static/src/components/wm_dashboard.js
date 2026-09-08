/** @odoo-module **/

import { Component, useState, onWillStart, onMounted, onWillDestroy, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { loadJS } from "@web/core/assets";
import { _t } from "@web/core/l10n/translation";

export class WmDashboard extends Component {
    static template = "wm_dashboard.Dashboard";

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.action = useService("action");
        this.state = useState({
            data: null,
            loading: true,
            lastRefreshed: null,
            activeTimeframe: 'today',
        });

        this.tonnageChartRef = useRef("tonnageChart");
        this.efficiencyChartRef = useRef("efficiencyChart");
        this.categoryChartRef = useRef("categoryChart");
        this.inspectionChartRef = useRef("inspectionChart");

        this._tonnageChart = null;
        this._efficiencyChart = null;
        this._categoryChart = null;
        this._inspectionChart = null;

        onWillStart(async () => {
            await loadJS("/web/static/lib/Chart/Chart.js");
            await this._loadData();
        });

        onMounted(() => {
            document.body.classList.add("wm_dashboard_active");
            if (this.state.data) {
                this._renderCharts();
            }
            // Auto refresh every 1 hour
            this.refreshInterval = setInterval(() => {
                this.onRefresh();
            }, 3600000);
        });

        onWillDestroy(() => {
            document.body.classList.remove("wm_dashboard_active");
            if (this.refreshInterval) {
                clearInterval(this.refreshInterval);
            }
        });
    }

    async _loadData() {
        this.state.loading = true;
        try {
            const data = await this.orm.call("wm.dashboard", "get_dashboard_data", [this.state.activeTimeframe]);
            this.state.data = data;
            this.state.lastRefreshed = new Date().toLocaleTimeString();
        } catch (error) {
            this.notification.add(_t("Failed to load dashboard data."), { type: "danger" });
        } finally {
            this.state.loading = false;
        }
    }

    async selectTimeframe(period) {
        if (this.state.activeTimeframe === period) return;
        this.state.activeTimeframe = period;
        await this._loadData();
        this._renderCharts();
    }

    async onRefresh() {
        await this._loadData();
        this._renderCharts();
    }

    _renderCharts() {
        this._renderTonnageChart();
        this._renderEfficiencyChart();
        this._renderCategoryChart();
        this._renderInspectionChart();
    }

    _renderTonnageChart() {
        const canvas = this.tonnageChartRef.el;
        if (!canvas || !this.state.data) return;

        if (this._tonnageChart) {
            this._tonnageChart.destroy();
            this._tonnageChart = null;
        }

        const data = this.state.data;
        const timeframe = this.state.activeTimeframe;
        let currentLabel = "Today";
        let priorLabel = "Same Day Last Week";
        if (timeframe === "week") {
            currentLabel = "This Week";
            priorLabel = "Prior Week";
        } else if (timeframe === "month") {
            currentLabel = "This Month";
            priorLabel = "Prior Month";
        }

        this._tonnageChart = new window.Chart(canvas.getContext("2d"), {
            type: "bar",
            data: {
                labels: data.tonnage_labels,
                datasets: [
                    {
                        label: currentLabel,
                        data: data.tonnage_today,
                        backgroundColor: "#10B981",
                        borderColor: "#10B981",
                        borderWidth: 0,
                        borderRadius: 4,
                    },
                    {
                        label: priorLabel,
                        data: data.tonnage_last_week,
                        backgroundColor: "rgba(16, 185, 129, 0.25)",
                        borderColor: "rgba(16, 185, 129, 0.3)",
                        borderWidth: 0,
                        borderRadius: 4,
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: "#0B1118",
                        titleColor: "#FFFFFF",
                        bodyColor: "#10B981",
                        borderColor: "#1E293B",
                        borderWidth: 1,
                        padding: 10,
                        cornerRadius: 8,
                        callbacks: {
                            label: (context) => {
                                const label = context.dataset.label || "";
                                const val = context.parsed.y !== null ? context.parsed.y : 0;
                                return ` ${label}: ${val} kg`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        ticks: { color: "#64748B", font: { size: 11, weight: "600" } },
                        grid: { display: false }
                    },
                    y: {
                        beginAtZero: true,
                        ticks: {
                            color: "#64748B",
                            font: { size: 11 },
                            callback: (value) => `${value} kg`
                        },
                        grid: { color: "#1E293B" }
                    }
                }
            }
        });
    }

    _renderEfficiencyChart() {
        const canvas = this.efficiencyChartRef.el;
        if (!canvas || !this.state.data) return;

        if (this._efficiencyChart) {
            this._efficiencyChart.destroy();
            this._efficiencyChart = null;
        }

        const data = this.state.data;
        this._efficiencyChart = new window.Chart(canvas.getContext("2d"), {
            type: "doughnut",
            data: {
                labels: ["On-Time", "Delayed"],
                datasets: [{
                    data: [data.on_time_pct, data.delayed_pct],
                    backgroundColor: ["#10B981", "#EF4444"],
                    borderColor: "#131C27",
                    borderWidth: 2,
                    hoverOffset: 8,
                    hoverBorderWidth: 0,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: "78%",
                layout: {
                    padding: 12
                },
                onClick: (event, elements) => {
                    if (elements && elements.length > 0) {
                        const index = elements[0].index;
                        if (index === 0) {
                            this.onEfficiencyClick('on_time');
                        } else if (index === 1) {
                            this.onEfficiencyClick('late');
                        }
                    }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: "#0B1118",
                        titleColor: "#FFFFFF",
                        bodyColor: "#10B981",
                        borderColor: "#1E293B",
                        borderWidth: 1,
                        padding: 8,
                        cornerRadius: 6,
                    }
                }
            }
        });
    }

    _renderCategoryChart() {
        const canvas = this.categoryChartRef.el;
        if (!canvas || !this.state.data) return;

        if (this._categoryChart) {
            this._categoryChart.destroy();
            this._categoryChart = null;
        }

        // Use timeframe-filtered stream_distribution (actual tonnage collected per category)
        // Falls back to catalogue material counts if no collection data exists for the period
        const streamData = this.state.data.stream_distribution || [];
        const catData = this.state.data.category_data || [];
        const displayData = streamData.length > 0 ? streamData : catData.filter(d => d.total > 0);
        const useTonnage = streamData.length > 0;

        const palette = [
            "#3B82F6", "#10B981", "#F59E0B", "#06B6D4",
            "#F97316", "#8B5CF6", "#EAB308", "#14B8A6"
        ];

        this._categoryChart = new window.Chart(canvas.getContext("2d"), {
            type: "doughnut",
            data: {
                labels: displayData.map((d) => d.code ? `${d.code} — ${d.name}` : d.name),
                datasets: [{
                    data: displayData.map((d) => useTonnage ? d.tonnage : d.total),
                    backgroundColor: palette.slice(0, displayData.length),
                    borderColor: "#131C27",
                    borderWidth: 2,
                    hoverOffset: 8,
                    hoverBorderWidth: 0,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: "55%",
                layout: {
                    padding: 12
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: "#0B1118",
                        titleColor: "#FFFFFF",
                        bodyColor: "#E5E7EB",
                        borderColor: "#1E293B",
                        borderWidth: 1,
                        padding: 8,
                        cornerRadius: 6,
                        callbacks: {
                            label: (context) => {
                                const val = context.parsed;
                                const unit = useTonnage ? ' kg' : ' materials';
                                return ` ${val}${unit}`;
                            }
                        }
                    },
                },
            },
        });
    }

    _renderInspectionChart() {
        const canvas = this.inspectionChartRef.el;
        if (!canvas || !this.state.data || !this.state.data.has_inspection) return;

        if (this._inspectionChart) {
            this._inspectionChart.destroy();
            this._inspectionChart = null;
        }

        const data = this.state.data;
        this._inspectionChart = new window.Chart(canvas.getContext("2d"), {
            type: "doughnut",
            data: {
                labels: ["Passed", "Failed", "Pending"],
                datasets: [{
                    data: [data.inspection_passed, data.inspection_failed, data.inspection_pending],
                    backgroundColor: ["#10B981", "#EF4444", "#475569"],
                    borderColor: "#131C27",
                    borderWidth: 2,
                    hoverOffset: 8,
                    hoverBorderWidth: 0,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: "78%",
                layout: {
                    padding: 12
                },
                onClick: (event, elements) => {
                    if (elements && elements.length > 0) {
                        const index = elements[0].index;
                        const states = ['passed', 'failed', 'pending'];
                        this.onInspectionStateClick(states[index]);
                    }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: "#0B1118",
                        titleColor: "#FFFFFF",
                        bodyColor: "#E5E7EB",
                        borderColor: "#1E293B",
                        borderWidth: 1,
                        padding: 8,
                        cornerRadius: 6,
                    }
                }
            }
        });
    }

    _getTimeframeDateRange() {
        const now = new Date();
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const day = String(now.getDate()).padStart(2, '0');
        const todayEndStr = `${year}-${month}-${day} 23:59:59`;
        const todayDateStr = `${year}-${month}-${day}`;

        let startDate = new Date();
        const timeframe = this.state.activeTimeframe || 'today';
        if (timeframe === 'week') {
            startDate.setDate(now.getDate() - 6);
        } else if (timeframe === 'month') {
            startDate = new Date(now.getFullYear(), now.getMonth(), 1);
        }

        const startYear = startDate.getFullYear();
        const startMonth = String(startDate.getMonth() + 1).padStart(2, '0');
        const startDay = String(startDate.getDate()).padStart(2, '0');
        const startDtStr = `${startYear}-${startMonth}-${startDay} 00:00:00`;
        const startDateStr = `${startYear}-${startMonth}-${startDay}`;

        return { startDtStr, todayEndStr, startDateStr, todayDateStr, timeframe };
    }

    onInspectionClick(resId) {
        if (!this.state.data || !this.state.data.can_access_inspection) return;
        if (!resId) return;
        this.action.doAction({
            name: "Batch Inspection",
            type: "ir.actions.act_window",
            res_model: "wm.batch.inspection",
            res_id: resId,
            views: [[false, "form"]],
            target: "current",
        });
    }

    onInspectionStateClick(state) {
        if (!this.state.data || !this.state.data.can_access_inspection) return;
        const { startDtStr, todayEndStr, timeframe } = this._getTimeframeDateRange();
        let domain = [['inspection_date', '>=', startDtStr], ['inspection_date', '<=', todayEndStr]];
        if (state === 'passed') {
            domain.push(['state', '=', 'passed']);
        } else if (state === 'failed') {
            domain.push(['state', '=', 'failed']);
        } else if (state === 'pending') {
            domain.push(['state', 'in', ['draft', 'in_progress']]);
        }
        const actionTitle = state && state !== 'all' ? `Batch Inspections - ${state.toUpperCase()} (${timeframe.toUpperCase()})` : `Batch Inspections (${timeframe.toUpperCase()})`;
        this.action.doAction({
            name: actionTitle,
            type: "ir.actions.act_window",
            res_model: "wm.batch.inspection",
            views: [[false, "list"], [false, "form"]],
            domain: domain,
            target: "current",
        });
    }

    onRevenueClick() {
        const data = this.state.data;
        if (!data) return;
        if (data.revenue_invoice > 0 || (!data.revenue_collection && !data.revenue_recycling)) {
            this.onRevenueSourceClick('invoice');
        } else if (data.revenue_collection > 0) {
            this.onRevenueSourceClick('collection');
        } else if (data.revenue_recycling > 0) {
            this.onRevenueSourceClick('recycling');
        } else {
            this.onRevenueSourceClick('invoice');
        }
    }

    onRevenueSourceClick(source) {
        const data = this.state.data;
        if (!data) return;

        // Use exact date strings the backend used — guarantees list sum == KPI sum
        const startDate = data.revenue_start_date;
        const endDate = data.revenue_end_date;
        const startDt = data.revenue_start_dt;
        const endDt = data.revenue_end_dt;
        const timeframe = this.state.activeTimeframe.toUpperCase();

        if (source === 'invoice') {
            if (!data.has_account || !data.can_access_account) {
                if (!data.has_account) this.notification.add(_t("Invoicing module is not installed."), { type: "warning" });
                return;
            }
            this.action.doAction({
                name: `Customer Invoices (${timeframe})`,
                type: "ir.actions.act_window",
                res_model: "account.move",
                views: [[false, "list"], [false, "form"]],
                domain: [
                    ["move_type", "in", ["out_invoice", "out_refund"]],
                    ["state", "=", "posted"],
                    ["invoice_date", ">=", startDate],
                    ["invoice_date", "<=", endDate],
                ],
                target: "current",
            });
        } else if (source === 'collection') {
            if (!data.has_collection || !data.can_interact_collection) {
                if (!data.has_collection) this.notification.add(_t("Collection module is not installed."), { type: "warning" });
                return;
            }
            const orderStates = data.has_account
                ? ['completed', 'signed', 'in_progress']
                : ['completed', 'signed', 'invoiced', 'in_progress'];
            this.action.doAction({
                name: `Collection Orders — Revenue (${timeframe})`,
                type: "ir.actions.act_window",
                res_model: "wm.collection.order",
                views: [[false, "list"], [false, "form"]],
                domain: [
                    "|",
                    "&", ["scheduled_start", ">=", startDt], ["scheduled_start", "<=", endDt],
                    "&", ["scheduled_start", "=", false], "&", ["create_date", ">=", startDt], ["create_date", "<=", endDt],
                    ["state", "in", orderStates],
                ],
                target: "current",
            });
        } else if (source === 'recycling') {
            if (!data.has_recycling) {
                this.notification.add(_t("Recycling module is not installed."), { type: "warning" });
                return;
            }
            this.action.doAction({
                name: `Recycling Orders — Revenue (${timeframe})`,
                type: "ir.actions.act_window",
                res_model: "recycling.order",
                views: [[false, "list"], [false, "form"]],
                domain: [
                    ["state", "=", "done"],
                    ["date_done", ">=", startDt],
                    ["date_done", "<=", endDt],
                ],
                target: "current",
            });
        }
    }

    onRouteClick(state) {
        if (!this.state.data || !this.state.data.has_collection || !this.state.data.can_interact_collection) {
            if (!this.state.data || !this.state.data.has_collection) {
                this.notification.add(_t("Collection module is not installed."), { type: "warning" });
            }
            return;
        }

        const { startDtStr, todayEndStr, timeframe } = this._getTimeframeDateRange();

        let domain = [
            "|",
            "&", ["scheduled_start", ">=", startDtStr], ["scheduled_start", "<=", todayEndStr],
            "&", ["scheduled_start", "=", false], "&", ["create_date", ">=", startDtStr], ["create_date", "<=", todayEndStr],
        ];
        if (state === 'pending') {
            domain.push(['state', 'in', ['draft', 'scheduled']]);
        } else if (state === 'in_progress') {
            domain.push(['state', 'in', ['dispatched', 'in_progress']]);
        } else if (state === 'completed') {
            domain.push(['state', 'in', ['completed', 'signed', 'invoiced']]);
        }

        const actionTitle = state && state !== 'all' ? `Collection Orders - ${state.toUpperCase()} (${timeframe.toUpperCase()})` : `Collection Orders (${timeframe.toUpperCase()})`;
        this.action.doAction({
            name: actionTitle,
            type: 'ir.actions.act_window',
            res_model: 'wm.collection.order',
            views: [[false, 'list'], [false, 'form']],
            domain: domain,
            target: 'current',
        });
    }

    onFleetClick(status) {
        if (!this.state.data || !this.state.data.has_fleet || !this.state.data.can_access_fleet) {
            if (!this.state.data || !this.state.data.has_fleet) {
                this.notification.add(_t("Fleet module is not installed."), { type: "warning" });
            }
            return;
        }
        let domain = [];
        if (status === 'available') {
            domain = [['id', 'in', this.state.data.fleet_available_ids || []]];
        } else if (status === 'dispatched') {
            domain = [['id', 'in', this.state.data.fleet_dispatched_ids || []]];
        } else if (status === 'maintenance') {
            domain = [['id', 'in', this.state.data.fleet_maintenance_ids || []]];
        } else {
            domain = [];
        }
        const actionTitle = status && status !== 'all' ? `Fleet Vehicles - ${status.toUpperCase()}` : 'Fleet Vehicles';
        this.action.doAction({
            name: actionTitle,
            type: 'ir.actions.act_window',
            res_model: 'fleet.vehicle',
            views: [[false, 'list'], [false, 'form']],
            domain: domain,
            target: 'current',
        });
    }

    onManifestClick(resId) {
        if (!this.state.data || !this.state.data.can_interact_collection) return;
        if (!resId) return;
        this.action.doAction({
            name: "Collection Order",
            type: "ir.actions.act_window",
            res_model: "wm.collection.order",
            res_id: resId,
            views: [[false, "form"]],
            target: "current",
        });
    }

    onEfficiencyClick(type) {
        if (!this.state.data || !this.state.data.has_collection || !this.state.data.can_interact_collection) {
            if (!this.state.data || !this.state.data.has_collection) {
                this.notification.add(_t("Collection module is not installed."), { type: "warning" });
            }
            return;
        }
        let domain = [];
        if (type === 'on_time') {
            domain = [['id', 'in', this.state.data.efficiency_on_time_ids || []]];
        } else if (type === 'late') {
            domain = [['id', 'in', this.state.data.efficiency_late_ids || []]];
        }
        this.action.doAction({
            name: `Collection Orders - ${type === 'on_time' ? 'ON-TIME' : 'LATE'}`,
            type: 'ir.actions.act_window',
            res_model: 'wm.collection.order',
            views: [[false, 'list'], [false, 'form']],
            domain: domain,
            target: 'current',
        });
    }

    onViewAllAwaitingSignature() {
        if (!this.state.data || !this.state.data.has_collection || !this.state.data.can_interact_collection) {
            if (!this.state.data || !this.state.data.has_collection) {
                this.notification.add(_t("Collection module is not installed."), { type: "warning" });
            }
            return;
        }
        this.action.doAction({
            name: "Collection Orders Awaiting Signature",
            type: "ir.actions.act_window",
            res_model: "wm.collection.order",
            views: [[false, "list"], [false, "form"]],
            domain: [["state", "in", ["completed", "in_progress", "scheduled"]]],
            target: "current",
        });
    }

    get ordersProgressStyle() {
        if (!this.state.data) {
            return { pending: '0%', in_progress: '0%', completed: '0%' };
        }
        const pending = this.state.data.pending_count || 0;
        const inProgress = this.state.data.in_progress_count || 0;
        const completed = this.state.data.completed_count || 0;
        const total = pending + inProgress + completed;
        if (!total) {
            return { pending: '0%', in_progress: '0%', completed: '0%' };
        }
        const pendingPct = ((pending / total) * 100).toFixed(1);
        const inProgressPct = ((inProgress / total) * 100).toFixed(1);
        const completedPct = (100.0 - parseFloat(pendingPct) - parseFloat(inProgressPct)).toFixed(1);
        return {
            pending: `${pendingPct}%`,
            in_progress: `${inProgressPct}%`,
            completed: `${completedPct}%`,
        };
    }

    get inspectionProgressStyle() {
        if (!this.state.data) {
            return { passed: '0%', failed: '0%', pending: '0%' };
        }
        const passed = this.state.data.inspection_passed || 0;
        const failed = this.state.data.inspection_failed || 0;
        const pending = this.state.data.inspection_pending || 0;
        const total = passed + failed + pending;
        if (!total) {
            return { passed: '0%', failed: '0%', pending: '0%' };
        }
        const passedPct = ((passed / total) * 100).toFixed(1);
        const failedPct = ((failed / total) * 100).toFixed(1);
        const pendingPct = (100.0 - parseFloat(passedPct) - parseFloat(failedPct)).toFixed(1);
        return {
            passed: `${passedPct}%`,
            failed: `${failedPct}%`,
            pending: `${pendingPct}%`,
        };
    }

    get revenueTrend() {
        if (!this.state.data) return { label: '', cssClass: '', pct: '' };
        const cur = this.state.data.revenue_cur_month || 0;
        const prior = this.state.data.revenue_prior_month || 0;
        if (prior === 0 && cur === 0) return { label: '—', cssClass: 'kpi_badge_neutral', pct: '' };
        if (prior === 0) return { label: '▲ NEW', cssClass: 'kpi_badge_new', pct: '' };
        const pct = ((cur - prior) / prior) * 100;
        if (pct > 0) return { label: `▲ ${pct.toFixed(1)}%`, cssClass: 'kpi_badge_up', pct: pct.toFixed(1) };
        if (pct < 0) return { label: `▼ ${Math.abs(pct).toFixed(1)}%`, cssClass: 'kpi_badge_down', pct: Math.abs(pct).toFixed(1) };
        return { label: '— 0%', cssClass: 'kpi_badge_neutral', pct: '0' };
    }

    formatCurrency(val) {
        if (val === undefined || val === null || isNaN(val)) return "0.00";
        return Number(val).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }
}

registry.category("actions").add("wm_dashboard.Dashboard", WmDashboard);
