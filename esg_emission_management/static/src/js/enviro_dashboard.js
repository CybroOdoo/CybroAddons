/** @odoo-module **/

import { Component, onWillStart, useState, useExternalListener, useRef, onMounted } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { loadJS } from "@web/core/assets";

const MONTH_NAMES = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
const QUARTER_RANGES = { 1: "Jan – Mar", 2: "Apr – Jun", 3: "Jul – Sep", 4: "Oct – Dec" };

function pad2(n) { return String(n).padStart(2, "0"); }
function lastDayOf(year, month) { return new Date(year, month, 0).getDate(); }

const STORAGE_KEY = "enviro_dashboard_filter";

export class EnviroDashboard extends Component {
    static template = "esg_emission_management.EnviroDashboard";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");

        const today = new Date();
        const year = today.getFullYear();
        const month = today.getMonth() + 1;
        const quarter = Math.ceil(month / 3);

        const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || "null") || {};

        this.state = useState({
            data: {
                year: "",
                total: 0, scope1: 0, scope2: 0, scope3: 0,
                retired_offsets: 0, net_total: 0, missing_count: 0,
                scope1_pct: 0, scope2_pct: 0, scope3_pct: 0,
                target_progress: 0, target_reduction_pct: 0, target_baseline: 0,
                active_initiatives_count: 0,
                initiative_expected_saving: 0, initiative_actual_saving: 0,
                months: [], recent_entries: [], recent_initiatives: [],
            },
            filter: {
                mode:       saved.mode       ?? "year",
                year:       saved.year       ?? year,
                month:      saved.month      ?? month,
                quarter:    saved.quarter    ?? quarter,
                customFrom: saved.customFrom ?? "",
                customTo:   saved.customTo   ?? "",
                open: false,
                scopes: saved.scopes ?? { scope1: true, scope2: true, scope3: true },
                scopesOpen: false,
            },
        });

        this.monthChartRef = useRef("monthChart");
        this.categoryChartRef = useRef("categoryChart");
        this.scopeChartRef = useRef("scopeChart");
        this.siteChartRef = useRef("siteChart");
        this.activityChartRef = useRef("activityChart");

        useExternalListener(window, "click", () => {
            this.state.filter.open = false;
            this.state.filter.scopesOpen = false;
        });

        onWillStart(async () => {
            await loadJS("/web/static/lib/Chart/Chart.js");
            await this._reload();
        });

        onMounted(() => {
            if (this.state.data.months.length) {
                this.renderCharts();
            }
        });
    }

    // ── Period label helpers ──────────────────────────────────────────────────

    get periodLabel() {
        const { mode, year, month, quarter, customFrom, customTo } = this.state.filter;
        if (mode === "year")    return String(year);
        if (mode === "quarter") return `${QUARTER_RANGES[quarter]} ${year}`;
        if (mode === "month")   return `${MONTH_NAMES[month - 1]} ${year}`;
        if (customFrom && customTo) return `${customFrom} – ${customTo}`;
        return "Custom";
    }

    get periodSubtitle() {
        const { mode, year, month, quarter, customFrom, customTo } = this.state.filter;
        if (mode === "year")    return `FY ${year}`;
        if (mode === "quarter") return `${QUARTER_RANGES[quarter]} ${year}`;
        if (mode === "month")   return `${MONTH_NAMES[month - 1]} ${year}`;
        if (customFrom && customTo) return `${customFrom} – ${customTo}`;
        return "Custom range";
    }

    rowLabel(mode) {
        const { year, month, quarter } = this.state.filter;
        if (mode === "year")    return String(year);
        if (mode === "quarter") return `${QUARTER_RANGES[quarter]} ${year}`;
        if (mode === "month")   return `${MONTH_NAMES[month - 1]} ${year}`;
        return "";
    }

    // ── Date range calculation ────────────────────────────────────────────────

    _getDateRange() {
        const { mode, year, month, quarter, customFrom, customTo } = this.state.filter;
        if (mode === "year") {
            return { date_from: `${year}-01-01`, date_to: `${year}-12-31` };
        }
        if (mode === "quarter") {
            const sm = (quarter - 1) * 3 + 1;
            const em = sm + 2;
            return {
                date_from: `${year}-${pad2(sm)}-01`,
                date_to:   `${year}-${pad2(em)}-${pad2(lastDayOf(year, em))}`,
            };
        }
        if (mode === "month") {
            return {
                date_from: `${year}-${pad2(month)}-01`,
                date_to:   `${year}-${pad2(month)}-${pad2(lastDayOf(year, month))}`,
            };
        }
        if (mode === "custom" && customFrom && customTo) {
            return { date_from: customFrom, date_to: customTo };
        }
        const y = new Date().getFullYear();
        return { date_from: `${y}-01-01`, date_to: `${y}-12-31` };
    }

    get scopeLabel() {
        const { scope1, scope2, scope3 } = this.state.filter.scopes;
        if (scope1 && scope2 && scope3) return "All Scopes";
        const names = [];
        if (scope1) names.push("Direct");
        if (scope2) names.push("Indirect");
        if (scope3) names.push("Other");
        return names.length ? names.join(", ") : "All Scopes";
    }

    toggleScopeDropdown(ev) {
        ev.stopPropagation();
        const f = this.state.filter;
        f.scopesOpen = !f.scopesOpen;
        f.open = false;
    }

    toggleScope(scope, ev) {
        ev.stopPropagation();
        const s = this.state.filter.scopes;
        s[scope] = !s[scope];
        // ensure at least one is selected
        if (!s.scope1 && !s.scope2 && !s.scope3) s[scope] = true;
        this._reload();
    }

    async _reload() {
        const { open, scopesOpen, ...toSave } = this.state.filter;
        localStorage.setItem(STORAGE_KEY, JSON.stringify(toSave));

        const { date_from, date_to } = this._getDateRange();
        const { scope1, scope2, scope3 } = this.state.filter.scopes;
        const scopes = [];
        if (scope1) scopes.push("scope1");
        if (scope2) scopes.push("scope2");
        if (scope3) scopes.push("scope3");
        this.state.data = await this.orm.call(
            "enviro.emission.record", "get_dashboard_data", [], { date_from, date_to, scopes }
        );
        // Only render if mounted (refs available)
        if (this.monthChartRef.el || this.categoryChartRef.el || this.scopeChartRef.el || this.siteChartRef.el || this.activityChartRef.el) {
            this.renderCharts();
        }
    }

    // ── Filter controls ───────────────────────────────────────────────────────

    toggleDropdown(ev) {
        ev.stopPropagation();
        this.state.filter.open = !this.state.filter.open;
    }

    stopProp(ev) { ev.stopPropagation(); }

    /** Navigate the active mode forward/backward one step (main arrows). */
    navigate(direction) {
        this._shiftPeriod(this.state.filter.mode, direction);
        this._reload();
    }

    /** Navigate a specific row's period without changing the active mode. */
    navigateRow(mode, direction, ev) {
        ev.stopPropagation();
        this._shiftPeriod(mode, direction);
        if (this.state.filter.mode === mode) this._reload();
    }

    _shiftPeriod(mode, dir) {
        const f = this.state.filter;
        if (mode === "year") {
            f.year += dir;
        } else if (mode === "quarter") {
            f.quarter += dir;
            if (f.quarter < 1) { f.quarter = 4; f.year--; }
            if (f.quarter > 4) { f.quarter = 1; f.year++; }
        } else if (mode === "month") {
            f.month += dir;
            if (f.month < 1)  { f.month = 12; f.year--; }
            if (f.month > 12) { f.month = 1;  f.year++; }
        }
    }

    setMode(mode, ev) {
        ev.stopPropagation();
        const f = this.state.filter;
        f.mode = mode;
        if (mode !== "custom") {
            f.open = false;
            this._reload();
        }
    }

    applyCustom() {
        const f = this.state.filter;
        if (f.customFrom && f.customTo) {
            f.open = false;
            this._reload();
        }
    }

    onCustomFrom(ev) { this.state.filter.customFrom = ev.target.value; }
    onCustomTo(ev)   { this.state.filter.customTo   = ev.target.value; }

    // ── Chart helpers ─────────────────────────────────────────────────────────

    get targetGaugeStyle() {
        const p = this.state.data.target_progress || 0;
        return `background: conic-gradient(#1f9d75 ${p}%, #e2e8f0 0);`;
    }

    renderCharts() {
        if (!window.Chart) return;

        // Month Chart
        const monthCanvas = this.monthChartRef.el;
        if (monthCanvas) {
            if (this.monthChart) this.monthChart.destroy();
            if (this.state.data.months.length) {
                this.monthChart = new Chart(monthCanvas, {
                    type: 'bar',
                    data: {
                        labels: this.state.data.months.map(m => m.label.split(' ')[0]),
                        datasets: [{
                            label: 'tCO2e',
                            data: this.state.data.months.map(m => m.value),
                            backgroundColor: '#1f9d75',
                            borderRadius: 4,
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: { legend: { display: false } },
                        scales: { y: { beginAtZero: true } }
                    }
                });
            }
        }

        // Scope Chart
        const scopeCanvas = this.scopeChartRef.el;
        if (scopeCanvas) {
            if (this.scopeChart) this.scopeChart.destroy();
            const { scope1, scope2, scope3 } = this.state.data;
            if (scope1 > 0 || scope2 > 0 || scope3 > 0) {
                this.scopeChart = new Chart(scopeCanvas, {
                    type: 'doughnut',
                    data: {
                        labels: ['Scope 1', 'Scope 2', 'Scope 3'],
                        datasets: [{
                            data: [scope1, scope2, scope3],
                            backgroundColor: ['#1f9d75', '#2f80d8', '#f59d23'],
                            borderWidth: 0,
                            hoverOffset: 4
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        cutout: '70%',
                        plugins: {
                            legend: { position: 'right', labels: { usePointStyle: true, boxWidth: 8 } }
                        },
                        onClick: (e, elements) => {
                            if (!elements || elements.length === 0) return;
                            const index = elements[0].index;
                            const scopeKey = ['scope1', 'scope2', 'scope3'][index];
                            if (!scopeKey) return;
                            this.openEntries([...this._filterDomain(), ['scope', '=', scopeKey]]);
                        }
                    }
                });
            }
        }

        // Category Chart
        const catCanvas = this.categoryChartRef.el;
        if (catCanvas) {
            if (this.categoryChart) this.categoryChart.destroy();
            if (this.state.data.categories && this.state.data.categories.length) {
                this.categoryChart = new Chart(catCanvas, {
                    type: 'pie',
                    data: {
                        labels: this.state.data.categories.map(c => c.label),
                        datasets: [{
                            data: this.state.data.categories.map(c => c.value),
                            backgroundColor: ['#1f9d75', '#2f80d8', '#f59d23', '#8b5cf6', '#ec4899', '#14b8a6', '#64748b'],
                            borderWidth: 0,
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { position: 'right', labels: { usePointStyle: true, boxWidth: 8 } }
                        },
                        onClick: (e, elements) => {
                            if (!elements || elements.length === 0) return;
                            const index = elements[0].index;
                            const cat = this.state.data.categories && this.state.data.categories[index];
                            if (!cat) return;
                            this.openEntries([...this._filterDomain(), ['category', '=', cat.label.toLowerCase()]]);
                        }
                    }
                });
            }
        }

        // Site Chart
        const siteCanvas = this.siteChartRef?.el;
        if (siteCanvas) {
            if (this.siteChart) { this.siteChart.destroy(); this.siteChart = null; }
            if (this.state.data.sites && this.state.data.sites.length) {
                this.siteChart = new Chart(siteCanvas, {
                    type: 'bar',
                    data: {
                        labels: this.state.data.sites.map(s => s.label),
                        datasets: [{
                            label: 'tCO2e',
                            data: this.state.data.sites.map(s => s.value),
                            backgroundColor: '#8b5cf6',
                            borderRadius: 4,
                        }]
                    },
                    options: {
                        indexAxis: 'y',
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: { legend: { display: false } },
                        scales: { x: { beginAtZero: true } },
                        onClick: (e, elements) => {
                            if (!elements || elements.length === 0) return;
                            const index = elements[0].index;
                            const site = this.state.data.sites && this.state.data.sites[index];
                            if (!site) return;
                            this.openEntries([...this._filterDomain(), ['site_id.name', '=', site.label]]);
                        }
                    }
                });
            }
        }

        // Activity Chart
        const activityCanvas = this.activityChartRef?.el;
        if (activityCanvas) {
            if (this.activityChart) { this.activityChart.destroy(); this.activityChart = null; }
            if (this.state.data.activities && this.state.data.activities.length) {
                this.activityChart = new Chart(activityCanvas, {
                    type: 'doughnut',
                    data: {
                        labels: this.state.data.activities.map(a => a.label),
                        datasets: [{
                            data: this.state.data.activities.map(a => a.value),
                            backgroundColor: ['#1f9d75', '#2f80d8', '#f59d23', '#8b5cf6', '#ec4899', '#14b8a6', '#64748b'],
                            borderWidth: 0,
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        cutout: '70%',
                        plugins: {
                            legend: { position: 'right', labels: { usePointStyle: true, boxWidth: 8 } }
                        },
                        onClick: (e, elements) => {
                            if (!elements || elements.length === 0) return;
                            const index = elements[0].index;
                            const activity = this.state.data.activities && this.state.data.activities[index];
                            if (!activity) return;
                            this.openEntries([...this._filterDomain(), ['enviro_activity_type_id.name', '=', activity.label]]);
                        }
                    }
                });
            }
        }
    }

    get maxInitiativeSaving() {
        return Math.max(
            ...this.state.data.recent_initiatives.flatMap((i) => [
                i.expected_saving_tonnes, i.actual_saving_tonnes,
            ]),
            1
        );
    }

    initiativeSavingWidth(initiative, field) {
        return `${Math.max((initiative[field] / this.maxInitiativeSaving) * 100, initiative[field] ? 4 : 0)}%`;
    }

    downloadChart(chartRefName, filename, ev) {
        if (ev) ev.stopPropagation();
        const canvas = this[chartRefName + "Ref"]?.el;
        if (canvas) {
            const link = document.createElement("a");
            link.download = filename + ".png";
            link.href = canvas.toDataURL("image/png");
            link.click();
        }
    }

    // ── Navigation shortcuts ──────────────────────────────────────────────────

    /** Returns domain clauses for date + scope only (no state constraint). */
    _periodDomain() {
        const { date_from, date_to } = this._getDateRange();
        const { scope1, scope2, scope3 } = this.state.filter.scopes;
        const clauses = [
            ['date', '>=', date_from],
            ['date', '<=', date_to],
        ];
        const allScopes = scope1 && scope2 && scope3;
        if (!allScopes) {
            const active = [];
            if (scope1) active.push('scope1');
            if (scope2) active.push('scope2');
            if (scope3) active.push('scope3');
            if (active.length) clauses.push(['scope', 'in', active]);
        }
        return clauses;
    }

    /** Returns domain clauses for the currently active period + scope filters (state=logged). */
    _filterDomain() {
        return [['state', '=', 'logged'], ...this._periodDomain()];
    }

    openEntries(domain = []) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Emission Records",
            res_model: "enviro.emission.record",
            views: [[false, "list"], [false, "form"], [false, "pivot"], [false, "graph"]],
            domain,
        });
    }

    openReports()     { this.action.doAction("esg_emission_management.enviro_emission_record_reporting_action"); }
    openFactors()     { this.action.doAction("esg_emission_management.enviro_emission_factor_action"); }
    openTargets()     { this.action.doAction("esg_emission_management.enviro_target_action"); }

    openInitiatives(domain = []) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Reduction Initiatives",
            res_model: "enviro.initiative",
            views: [[false, "list"], [false, "form"]],
            domain,
        });
    }
}

registry.category("actions").add("esg_emission_management.dashboard", EnviroDashboard);
