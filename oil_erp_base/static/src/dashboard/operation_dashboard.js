/** @odoo-module **/
import { Component, useState, onWillStart, useEffect } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { loadJS } from "@web/core/assets";

export class OperationDashboard extends Component {
    static template = "oil_erp_base.OperationDashboard";
    static props = {
        action: { type: Object, optional: true },
        actionId: { type: Number, optional: true },
        updateActionState: { type: Function, optional: true },
        className: { type: String, optional: true },
        globalState: { type: Object, optional: true },
    };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.actionContext = this.props.action?.context || {};
        const operation = this.actionContext.operation || this._inferOperationFromTag();
        this.state = useState({
            operation,
            title: this._getDefaultTitle(operation),
            data: this._emptyData(),
            isLoading: true,
            error: null,
        });

        this.charts = {};

        onWillStart(async () => {
            await loadJS("/web/static/lib/Chart/Chart.js");
            await this._fetchDashboardData();
        });

        useEffect(() => {
            this._renderCharts();
            return () => this._destroyCharts();
        }, () => [this.state.data.charts]);
    }

    _destroyCharts() {
        Object.values(this.charts).forEach(chart => {
            if (chart && typeof chart.destroy === 'function') {
                chart.destroy();
            }
        });
        this.charts = {};
    }

    _renderCharts() {
        if (!this.state.data || !this.state.data.charts) return;

        this.state.data.charts.forEach(chartConfig => {
            const canvas = document.getElementById(`chart_${chartConfig.id}`);
            if (!canvas) return;

            if (this.charts[chartConfig.id]) {
                this.charts[chartConfig.id].destroy();
            }

            try {
                this.charts[chartConfig.id] = new window.Chart(canvas, {
                    type: chartConfig.type || 'bar',
                    data: chartConfig.data,
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'bottom',
                            }
                        },
                        ...chartConfig.options
                    }
                });
            } catch (err) {
                console.error("Chart rendering error:", err);
            }
        });
    }

    async _fetchDashboardData() {
        this.state.isLoading = true;
        this.state.error = null;
        try {
            const model = this._getDashboardModel();
            const result = await this.orm.call(model, "get_dashboard_data", [], {
                context: this.actionContext,
            });
            this.state.data = { ...this._emptyData(), ...(result || {}) };
        } catch (err) {
            console.error("Dashboard fetch error:", err);
            this.state.error = err?.message || "Unable to load dashboard data.";
            this.state.data = this._emptyData();
        } finally {
            this.state.isLoading = false;
        }
    }

    _getDashboardModel() {
        const operation = this.state.operation || 'generic';
        const mapping = {
            'upstream': 'oil.dashboard.upstream',
            'midstream': 'oil.dashboard.midstream',
            'downstream': 'oil.dashboard.downstream',
            'hse': 'oil.dashboard.hse',
        };
        return mapping[operation] || 'oil.dashboard.base';
    }

    _emptyData() {
        return {
            tiles: [],
            charts: [],
            metrics: [],
            highlights: [],
        };
    }

    _inferOperationFromTag() {
        const tag = this.props.action?.tag || "";
        if (tag.includes("upstream")) {
            return "upstream";
        }
        if (tag.includes("midstream")) {
            return "midstream";
        }
        if (tag.includes("downstream")) {
            return "downstream";
        }
        return "generic";
    }

    _getDefaultTitle(operation) {
        const titles = {
            upstream: "E & P Operations",
            midstream: "Pipeline & Transport",
            downstream: "Refinery Operations",
            generic: "Dashboard",
        };
        return titles[operation] || titles.generic;
    }

    onTileClick(tile) {
        if (tile.action) {
            this.action.doAction(tile.action);
        }
    }
}

registry.category("actions").add("oil_upstream.dashboard", OperationDashboard);
registry.category("actions").add("oil_midstream.dashboard", OperationDashboard);
registry.category("actions").add("oil_downstream.dashboard", OperationDashboard);
registry.category("actions").add("oil_hse.dashboard", OperationDashboard);
