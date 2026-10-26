/** @odoo-module **/

import {Component, onWillStart, onWillUnmount, useEffect, useRef, useState} from "@odoo/owl";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";
import {loadJS} from "@web/core/assets";
import {_t} from "@web/core/l10n/translation";

// Trend chart of one watched parameter: recent approved results with the
// QA-approved normal range and the specification limits drawn on it.
const COLORS = {
    value: "#5295f8",
    outside: "#dc2626",
    mean: "#1f2937",
    range: "#f59e0b",
    spec: "#7c3aed",
};

export class PharmaTrendControlChart extends Component {
    static template = "pharma_trend_monitoring.ControlChart";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.canvasRef = useRef("canvas");
        const params = this.props.action?.params || {};
        this.state = useState({
            parameters: [],
            parameterId: params.trend_parameter_id || false,
            limit: 60,
            data: null,
        });

        onWillStart(async () => {
            await loadJS("/web/static/lib/Chart/Chart.js");
            this.state.parameters = await this.orm.searchRead(
                "pharma.trend.parameter",
                [["is_trended", "=", true]],
                ["name"],
                {order: "product_id, stage, parameter_name"}
            );
            if (!this.state.parameterId && this.state.parameters.length) {
                this.state.parameterId = this.state.parameters[0].id;
            }
            await this.loadData();
        });

        useEffect(
            () => this.renderChart(),
            () => [this.state.data]
        );
        onWillUnmount(() => this.chart?.destroy());
    }

    async loadData() {
        if (!this.state.parameterId) {
            this.state.data = null;
            return;
        }
        this.state.data = await this.orm.call(
            "pharma.trend.parameter",
            "get_chart_data",
            [[this.state.parameterId]],
            {limit: this.state.limit}
        );
    }

    async onParameterChange(ev) {
        this.state.parameterId = parseInt(ev.target.value) || false;
        await this.loadData();
    }

    async onLimitChange(ev) {
        this.state.limit = parseInt(ev.target.value) || 0;
        await this.loadData();
    }

    openParameter() {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "pharma.trend.parameter",
            res_id: this.state.parameterId,
            views: [[false, "form"]],
        });
    }

    fmt(value) {
        return value === false || value === undefined || value === null ? "—" : value.toFixed(4);
    }

    get stateLabel() {
        const data = this.state.data;
        if (!data) {
            return "";
        }
        return data.range
            ? _t("Normal range approved %s", data.range.approved_on)
            : _t("Collecting results — %(count)s of %(min)s", {
                count: data.result_count,
                min: data.min_history,
            });
    }

    renderChart() {
        this.chart?.destroy();
        this.chart = null;
        const data = this.state.data;
        if (!this.canvasRef.el || !data || !data.points.length) {
            return;
        }
        const points = data.points;
        const labels = points.map((p) => p.lot);
        const line = (label, value, color, dash) => ({
            type: "line",
            label,
            data: labels.map(() => value),
            borderColor: color,
            borderWidth: 1.5,
            borderDash: dash,
            pointRadius: 0,
            pointHitRadius: 0,
            fill: false,
        });
        const color = (p) => (p.outside ? COLORS.outside : COLORS.value);
        const datasets = [{
            type: "line",
            label: _t("Result"),
            data: points.map((p) => p.value),
            borderColor: COLORS.value,
            borderWidth: 1.5,
            pointRadius: points.map((p) => (p.outside ? 6 : 4)),
            pointBackgroundColor: points.map(color),
            pointBorderColor: points.map(color),
            tension: 0,
            order: 0,
        }];
        const rangeLow = _t("Range low");
        const specMin = _t("Spec. min");
        if (data.range) {
            datasets.push(
                line(_t("Mean"), data.range.mean, COLORS.mean, []),
                line(_t("Normal range"), data.range.high, COLORS.range, [6, 4]),
                line(rangeLow, data.range.low, COLORS.range, [6, 4])
            );
        }
        if (data.spec.max !== false) {
            datasets.push(line(_t("Specification"), data.spec.max, COLORS.spec, []));
        }
        if (data.spec.min !== false) {
            datasets.push(line(data.spec.max !== false ? specMin : _t("Specification"),
                data.spec.min, COLORS.spec, []));
        }
        const hiddenLegend = [rangeLow, specMin];
        this.chart = new Chart(this.canvasRef.el.getContext("2d"), {
            type: "line",
            data: {labels, datasets},
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: false,
                interaction: {mode: "nearest", intersect: true},
                onClick: (ev, elements) => {
                    const hit = elements.find((el) => el.datasetIndex === 0);
                    if (hit) {
                        this.action.doAction({
                            type: "ir.actions.act_window",
                            res_model: "pharma.qc.test.order",
                            res_id: points[hit.index].order_id,
                            views: [[false, "form"]],
                        });
                    }
                },
                plugins: {
                    legend: {
                        position: "bottom",
                        labels: {
                            usePointStyle: true,
                            boxWidth: 10,
                            filter: (item) => !hiddenLegend.includes(item.text),
                        },
                    },
                    tooltip: {
                        filter: (item) => item.datasetIndex === 0,
                        callbacks: {
                            title: (items) => {
                                const p = points[items[0].dataIndex];
                                return `${p.lot} — ${p.date.slice(0, 10)}`;
                            },
                            label: (item) => {
                                const p = points[item.dataIndex];
                                const lines = [_t("Value: %(value)s %(uom)s", {
                                    value: p.value.toFixed(4),
                                    uom: data.uom,
                                })];
                                if (p.outside) {
                                    lines.push(_t("Outside normal range"));
                                }
                                return lines;
                            },
                        },
                    },
                },
                scales: {
                    x: {
                        grid: {display: false},
                        ticks: {color: "#6b7280", maxRotation: 60, autoSkip: true},
                    },
                    y: {
                        grid: {color: "rgba(82, 149, 248, 0.12)"},
                        ticks: {color: "#6b7280"},
                        title: {display: !!data.uom, text: data.uom},
                    },
                },
            },
        });
    }
}

registry.category("actions").add("pharma_trend_control_chart", PharmaTrendControlChart);
