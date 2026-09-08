/** @odoo-module **/

import { Component, useState, onWillStart, onMounted, onWillDestroy, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { loadJS } from "@web/core/assets";
import { _t } from "@web/core/l10n/translation";

export class WmComplianceDashboard extends Component {
    static template = "wm_compliance.Dashboard";

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.action = useService("action");
        this.state = useState({
            data: null,
            loading: true,
            lastRefreshed: null,
            activeTimeframe: "month",
        });

        this.streamChartRef = useRef("streamChart");
        this.targetChartRef = useRef("targetChart");
        this.certificateChartRef = useRef("certificateChart");
        this.streamShareChartRef = useRef("streamShareChart");

        this._streamChart = null;
        this._targetChart = null;
        this._certificateChart = null;
        this._streamShareChart = null;

        onWillStart(async () => {
            await loadJS("/web/static/lib/Chart/Chart.js");
            await this._loadData();
        });

        onMounted(() => {
            document.body.classList.add("wm_compliance_dashboard_active");
            if (this.state.data) {
                this._renderCharts();
            }
            // Auto refresh every 1 hour
            this.refreshInterval = setInterval(() => {
                this.onRefresh();
            }, 3600000);
        });

        onWillDestroy(() => {
            document.body.classList.remove("wm_compliance_dashboard_active");
            if (this.refreshInterval) {
                clearInterval(this.refreshInterval);
            }
            this._destroyCharts();
        });
    }

    async _loadData() {
        this.state.loading = true;
        try {
            const data = await this.orm.call("wm.compliance.dashboard", "get_dashboard_data", [this.state.activeTimeframe]);
            this.state.data = data;
            this.state.lastRefreshed = new Date().toLocaleTimeString();
        } catch (error) {
            this.notification.add(_t("Failed to load compliance dashboard data."), { type: "danger" });
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

    _destroyCharts() {
        if (this._streamChart) {
            this._streamChart.destroy();
            this._streamChart = null;
        }
        if (this._targetChart) {
            this._targetChart.destroy();
            this._targetChart = null;
        }
        if (this._certificateChart) {
            this._certificateChart.destroy();
            this._certificateChart = null;
        }
        if (this._streamShareChart) {
            this._streamShareChart.destroy();
            this._streamShareChart = null;
        }
    }

    _renderCharts() {
        this._renderStreamChart();
        this._renderTargetChart();
        this._renderCertificateChart();
        this._renderStreamShareChart();
    }

    _renderStreamChart() {
        const canvas = this.streamChartRef.el;
        if (!canvas || !this.state.data) return;

        if (this._streamChart) {
            this._streamChart.destroy();
            this._streamChart = null;
        }

        const data = this.state.data;
        const timeframe = this.state.activeTimeframe;
        let currentLabel = "Today";
        let priorLabel = "Yesterday";
        if (timeframe === "week") {
            currentLabel = "This Week";
            priorLabel = "Prior Week";
        } else if (timeframe === "month") {
            currentLabel = "This Month";
            priorLabel = "Prior Month";
        }

        this._streamChart = new window.Chart(canvas.getContext("2d"), {
            type: "bar",
            data: {
                labels: data.stream_labels || ["Hazardous", "Bio-Medical", "E-Waste", "C&D", "General"],
                datasets: [
                    {
                        label: currentLabel,
                        data: data.stream_selected_qty || [0, 0, 0, 0, 0],
                        backgroundColor: ["#EF4444", "#F97316", "#3B82F6", "#EAB308", "#10B981"],
                        borderRadius: 4,
                        borderWidth: 0,
                    },
                    {
                        label: priorLabel,
                        data: data.stream_prior_qty || [0, 0, 0, 0, 0],
                        backgroundColor: "rgba(100, 116, 139, 0.35)",
                        borderRadius: 4,
                        borderWidth: 0,
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
                },
                onClick: (event, elements) => {
                    if (elements && elements.length > 0) {
                        const index = elements[0].index;
                        const streamData = data.stream_data || [];
                        if (streamData[index]) {
                            this.onStreamClick(streamData[index].code, streamData[index].name);
                        }
                    }
                }
            }
        });
    }

    get targetHealthColorClass() {
        const d = this.state.data;
        if (!d || !d.total_targets || d.total_targets === 0) return "text_light";
        const pct = (d.targets_on_track / d.total_targets) * 100;
        if (pct >= 80) return "text_teal";
        if (pct >= 50) return "text_amber";
        return "text_red";
    }

    get targetHealthLabel() {
        const d = this.state.data;
        if (!d || !d.total_targets || d.total_targets === 0) return "TARGETS";
        const pct = (d.targets_on_track / d.total_targets) * 100;
        if (pct >= 80) return "ON TRACK";
        if (pct >= 50) return "AT RISK";
        return "BREACHED";
    }

    _renderTargetChart() {
        const canvas = this.targetChartRef.el;
        if (!canvas || !this.state.data) return;

        if (this._targetChart) {
            this._targetChart.destroy();
            this._targetChart = null;
        }

        const data = this.state.data;
        const total = (data.targets_on_track || 0) + (data.targets_at_risk || 0) + (data.targets_breached || 0);

        this._targetChart = new window.Chart(canvas.getContext("2d"), {
            type: "doughnut",
            data: {
                labels: total > 0 ? ["On Track", "At Risk", "Breached"] : ["No Targets"],
                datasets: [{
                    data: total > 0 ? [data.targets_on_track, data.targets_at_risk, data.targets_breached] : [1],
                    backgroundColor: total > 0 ? ["#10B981", "#F59E0B", "#EF4444"] : ["#334155"],
                    borderColor: "#131C27",
                    borderWidth: 2,
                    hoverOffset: total > 0 ? 6 : 0,
                    hoverBorderWidth: 0,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: "76%",
                layout: { padding: 4 },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        enabled: total > 0,
                        position: 'nearest',
                        yAlign: 'bottom',
                        caretPadding: 6,
                        backgroundColor: "#0B1118",
                        titleColor: "#FFFFFF",
                        bodyColor: "#E2E8F0",
                        borderColor: "#1E293B",
                        borderWidth: 1,
                        padding: 8,
                        cornerRadius: 6,
                        callbacks: {
                            label: (context) => {
                                const label = context.label || "";
                                const val = context.parsed !== null ? context.parsed : 0;
                                const pct = total > 0 ? Math.round((val / total) * 100) : 0;
                                return ` ${label}: ${val} (${pct}%)`;
                            }
                        }
                    }
                },
                onClick: (event, elements) => {
                    if (total > 0 && elements && elements.length > 0) {
                        const states = ['on_track', 'at_risk', 'breached'];
                        this.onTargetStateClick(states[elements[0].index]);
                    }
                }
            }
        });
    }

    _renderCertificateChart() {
        const canvas = this.certificateChartRef.el;
        if (!canvas || !this.state.data) return;

        if (this._certificateChart) {
            this._certificateChart.destroy();
            this._certificateChart = null;
        }

        const data = this.state.data;
        const total = (data.certificates_issued || 0) + (data.certificates_draft || 0);

        this._certificateChart = new window.Chart(canvas.getContext("2d"), {
            type: "doughnut",
            data: {
                labels: total > 0 ? ["Signed & Issued", "Draft Pending"] : ["No Certificates"],
                datasets: [{
                    data: total > 0 ? [data.certificates_issued, data.certificates_draft] : [1],
                    backgroundColor: total > 0 ? ["#10B981", "#64748B"] : ["#334155"],
                    borderColor: "#131C27",
                    borderWidth: 2,
                    hoverOffset: total > 0 ? 6 : 0,
                    hoverBorderWidth: 0,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: "76%",
                layout: { padding: 4 },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        enabled: total > 0,
                        position: 'nearest',
                        yAlign: 'bottom',
                        caretPadding: 6,
                        backgroundColor: "#0B1118",
                        titleColor: "#FFFFFF",
                        bodyColor: "#E2E8F0",
                        borderColor: "#1E293B",
                        borderWidth: 1,
                        padding: 8,
                        cornerRadius: 6,
                        callbacks: {
                            label: (context) => {
                                const label = context.label || "";
                                const val = context.parsed !== null ? context.parsed : 0;
                                const pct = total > 0 ? Math.round((val / total) * 100) : 0;
                                return ` ${label}: ${val} (${pct}%)`;
                            }
                        }
                    }
                },
                onClick: (event, elements) => {
                    if (total > 0 && elements && elements.length > 0) {
                        const states = ['issued', 'draft'];
                        this.onCertificateStateClick(states[elements[0].index]);
                    }
                }
            }
        });
    }

    _renderStreamShareChart() {
        const canvas = this.streamShareChartRef.el;
        if (!canvas || !this.state.data) return;

        if (this._streamShareChart) {
            this._streamShareChart.destroy();
            this._streamShareChart = null;
        }

        const allStreamData = this.state.data.stream_data || [];
        const activeStreamData = allStreamData.filter(s => s.quantity > 0);
        const hasData = activeStreamData.length > 0;

        const labels = hasData ? activeStreamData.map(s => s.name) : ["No Collections"];
        const values = hasData ? activeStreamData.map(s => s.quantity) : [1];
        const colors = hasData ? activeStreamData.map(s => s.color) : ["#1E293B"];

        this._streamShareChart = new window.Chart(canvas.getContext("2d"), {
            type: "doughnut",
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: colors,
                    borderColor: "#0E1622",
                    borderWidth: 2,
                    hoverOffset: hasData ? 6 : 0,
                    hoverBorderWidth: 0,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: "60%",
                layout: { padding: 4 },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        enabled: hasData,
                        backgroundColor: "#0B1118",
                        titleColor: "#FFFFFF",
                        bodyColor: "#E2E8F0",
                        borderColor: "#1E293B",
                        borderWidth: 1,
                        padding: 8,
                        cornerRadius: 6,
                        callbacks: {
                            label: (context) => {
                                const label = context.label || "";
                                const val = context.parsed !== null ? context.parsed : 0;
                                const total = this.state.data.total_stream_qty || values.reduce((a, b) => a + b, 0);
                                const pct = total > 0 ? ((val / total) * 100).toFixed(1) : 0;
                                return ` ${label}: ${val} kg (${pct}%)`;
                            }
                        }
                    }
                },
                onClick: (event, elements) => {
                    if (hasData && elements && elements.length > 0) {
                        const clicked = activeStreamData[elements[0].index];
                        if (clicked) {
                            this.onStreamClick(clicked.code, clicked.name);
                        }
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
        const todayStr = `${year}-${month}-${day}`;

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
        const startStr = `${startYear}-${startMonth}-${startDay}`;

        return { startStr, todayStr, timeframe };
    }

    // ── INTERACTIVE DRILLDOWNS ────────────────────────────────────────

    onManifestClick(resId) {
        if (!resId) return;
        this.action.doAction({
            name: "Compliance Manifest",
            type: "ir.actions.act_window",
            res_model: "wm.compliance.manifest",
            res_id: resId,
            views: [[false, "form"]],
            target: "current",
        });
    }

    onManifestStateClick(state) {
        const { startStr, todayStr, timeframe } = this._getTimeframeDateRange();
        const domain = [
            ['manifest_date', '>=', startStr],
            ['manifest_date', '<=', todayStr],
        ];
        if (state) {
            domain.push(['state', '=', state]);
        }
        const stateTitle = state ? state.toUpperCase() : 'ALL';
        this.action.doAction({
            name: `Compliance Manifests - ${stateTitle} (${timeframe.toUpperCase()})`,
            type: "ir.actions.act_window",
            res_model: "wm.compliance.manifest",
            views: [[false, "list"], [false, "form"]],
            domain: domain,
            target: "current",
        });
    }

    onStreamClick(streamCode, streamName) {
        const { startStr, todayStr, timeframe } = this._getTimeframeDateRange();
        let domain = [
            ['manifest_date', '>=', startStr],
            ['manifest_date', '<=', todayStr],
        ];
        let title = `Compliance Manifests (${timeframe.toUpperCase()})`;
        if (streamCode) {
            domain.push('|', ['line_ids.waste_category_id.code', '=', streamCode], ['line_ids.waste_category_id.name', '=', streamName || streamCode]);
            title = `Compliance Manifests - ${streamName || streamCode} (${timeframe.toUpperCase()})`;
        }
        this.action.doAction({
            name: title,
            type: "ir.actions.act_window",
            res_model: "wm.compliance.manifest",
            views: [[false, "list"], [false, "form"]],
            domain: domain,
            target: "current",
        });
    }

    onOverdueClick() {
        const today = new Date();
        today.setDate(today.getDate() - 7);
        const limitStr = today.toISOString().split('T')[0];
        this.action.doAction({
            name: "Overdue Compliance Manifests",
            type: "ir.actions.act_window",
            res_model: "wm.compliance.manifest",
            views: [[false, "list"], [false, "form"]],
            domain: [["state", "in", ["submitted", "collected"]], ["manifest_date", "<", limitStr]],
            target: "current",
        });
    }

    onPendingCustodyClick() {
        this.action.doAction({
            name: "Manifests Requiring Chain of Custody",
            type: "ir.actions.act_window",
            res_model: "wm.compliance.manifest",
            views: [[false, "list"], [false, "form"]],
            domain: [["state", "in", ["submitted", "collected"]], ["custody_ids", "=", false]],
            target: "current",
        });
    }

    onDocumentClick(resId) {
        if (!resId) return;
        this.action.doAction({
            name: "Permit & Licence",
            type: "ir.actions.act_window",
            res_model: "wm.compliance.document",
            res_id: resId,
            views: [[false, "form"]],
            target: "current",
        });
    }

    onExpiringDocsClick() {
        const today = new Date();
        const future = new Date();
        future.setDate(today.getDate() + 30);
        const todayStr = today.toISOString().split('T')[0];
        const futureStr = future.toISOString().split('T')[0];

        this.action.doAction({
            name: "Expiring Permits & Licences (30 Days)",
            type: "ir.actions.act_window",
            res_model: "wm.compliance.document",
            views: [[false, "list"], [false, "form"]],
            domain: [["expiry_date", ">=", todayStr], ["expiry_date", "<=", futureStr]],
            target: "current",
        });
    }

    onExpiredDocsClick() {
        const todayStr = new Date().toISOString().split('T')[0];
        this.action.doAction({
            name: "Expired Permits & Licences",
            type: "ir.actions.act_window",
            res_model: "wm.compliance.document",
            views: [[false, "list"], [false, "form"]],
            domain: [["expiry_date", "<", todayStr]],
            target: "current",
        });
    }

    onAllDocsClick() {
        this.action.doAction({
            name: "Compliance Document Vault",
            type: "ir.actions.act_window",
            res_model: "wm.compliance.document",
            views: [[false, "list"], [false, "form"]],
            target: "current",
        });
    }

    onTargetClick(resId) {
        if (!resId) return;
        this.action.doAction({
            name: "Compliance Target",
            type: "ir.actions.act_window",
            res_model: "wm.compliance.target",
            res_id: resId,
            views: [[false, "form"]],
            target: "current",
        });
    }

    onTargetStateClick(state) {
        const domain = state ? [["state", "=", state]] : [];
        this.action.doAction({
            name: `Compliance Targets - ${state ? state.toUpperCase() : 'ALL'}`,
            type: "ir.actions.act_window",
            res_model: "wm.compliance.target",
            views: [[false, "list"], [false, "form"]],
            domain: domain,
            target: "current",
        });
    }

    onCertificateClick(resId) {
        if (!resId) return;
        this.action.doAction({
            name: "Compliance Certificate",
            type: "ir.actions.act_window",
            res_model: "wm.compliance.certificate",
            res_id: resId,
            views: [[false, "form"]],
            target: "current",
        });
    }

    onCertificateStateClick(state) {
        const domain = state ? [["state", "=", state]] : [];
        this.action.doAction({
            name: `Compliance Certificates - ${state ? state.toUpperCase() : 'ALL'}`,
            type: "ir.actions.act_window",
            res_model: "wm.compliance.certificate",
            views: [[false, "list"], [false, "form"]],
            domain: domain,
            target: "current",
        });
    }

    openReportWizard() {
        if (!this.state.data || !this.state.data.can_access_report) {
            return;
        }
        this.action.doAction("wm_compliance.action_wm_compliance_report_wizard");
    }

    openAllManifests() {
        this.action.doAction({
            name: "All Compliance Manifests",
            type: "ir.actions.act_window",
            res_model: "wm.compliance.manifest",
            views: [[false, "list"], [false, "form"]],
            target: "current",
        });
    }

    openAllCertificates() {
        this.action.doAction({
            name: "All Compliance Certificates",
            type: "ir.actions.act_window",
            res_model: "wm.compliance.certificate",
            views: [[false, "list"], [false, "form"]],
            target: "current",
        });
    }

    openAllTargets() {
        this.action.doAction({
            name: "All Compliance Targets",
            type: "ir.actions.act_window",
            res_model: "wm.compliance.target",
            views: [[false, "list"], [false, "form"]],
            target: "current",
        });
    }

    openAllFacilities() {
        if (!this.state.data || !this.state.data.can_access_facility) {
            return;
        }
        this.action.doAction({
            name: "Disposal Facilities",
            type: "ir.actions.act_window",
            res_model: "wm.disposal.facility",
            views: [[false, "list"], [false, "form"]],
            target: "current",
        });
    }

    // ── PROGRESS BAR STYLES ──────────────────────────────────────────

    get manifestProgressStyle() {
        if (!this.state.data) {
            return { disposed: '0%', collected: '0%', submitted: '0%' };
        }
        const disposed = this.state.data.manifest_disposed || 0;
        const collected = this.state.data.manifest_collected || 0;
        const submitted = this.state.data.manifest_submitted || 0;
        const total = disposed + collected + submitted;
        if (!total) {
            return { disposed: '0%', collected: '0%', submitted: '0%' };
        }
        const dispPct = ((disposed / total) * 100).toFixed(1);
        const collPct = ((collected / total) * 100).toFixed(1);
        const submPct = (100.0 - parseFloat(dispPct) - parseFloat(collPct)).toFixed(1);
        return {
            disposed: `${dispPct}%`,
            collected: `${collPct}%`,
            submitted: `${submPct}%`,
        };
    }

    get targetProgressStyle() {
        if (!this.state.data) {
            return { on_track: '0%', at_risk: '0%', breached: '0%' };
        }
        const onTrack = this.state.data.targets_on_track || 0;
        const atRisk = this.state.data.targets_at_risk || 0;
        const breached = this.state.data.targets_breached || 0;
        const total = onTrack + atRisk + breached;
        if (!total) {
            return { on_track: '0%', at_risk: '0%', breached: '0%' };
        }
        const onTrackPct = ((onTrack / total) * 100).toFixed(1);
        const atRiskPct = ((atRisk / total) * 100).toFixed(1);
        const breachedPct = (100.0 - parseFloat(onTrackPct) - parseFloat(atRiskPct)).toFixed(1);
        return {
            on_track: `${onTrackPct}%`,
            at_risk: `${atRiskPct}%`,
            breached: `${breachedPct}%`,
        };
    }

    get documentProgressStyle() {
        if (!this.state.data) {
            return { valid: '0%', expiring: '0%', expired: '0%' };
        }
        const valid = this.state.data.active_valid_docs_count || 0;
        const expiring = this.state.data.expiring_docs_count || 0;
        const expired = this.state.data.expired_docs_count || 0;
        const total = valid + expiring + expired;
        if (!total) {
            return { valid: '0%', expiring: '0%', expired: '0%' };
        }
        const validPct = ((valid / total) * 100).toFixed(1);
        const expiringPct = ((expiring / total) * 100).toFixed(1);
        const expiredPct = (100.0 - parseFloat(validPct) - parseFloat(expiringPct)).toFixed(1);
        return {
            valid: `${validPct}%`,
            expiring: `${expiringPct}%`,
            expired: `${expiredPct}%`,
        };
    }
}

registry.category("actions").add("wm_compliance.Dashboard", WmComplianceDashboard);
