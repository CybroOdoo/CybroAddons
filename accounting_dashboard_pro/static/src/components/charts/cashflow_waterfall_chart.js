/** @odoo-module **/

import { Component, useRef, onMounted, onWillUpdateProps, onWillUnmount, onWillStart } from "@odoo/owl";
import { loadBundle } from "@web/core/assets";

export class CashflowWaterfallChart extends Component {
    static template = "accounting_dashboard_pro.CashflowWaterfallChart";
    static props = { data: { type: Object, optional: true }, formatCurrency: Function };

    setup() {
        this.canvasRef = useRef("canvas");
        this.chart = null;
        onWillStart(async () => {
            await loadBundle("web.chartjs_lib");
        });
        onMounted(() => this.renderChart());
        onWillUpdateProps((next) => {
            if (next.data !== this.props.data) {
                this.destroyChart();
                this.props = next;
                this.renderChart();
            }
        });
        onWillUnmount(() => this.destroyChart());
    }

    destroyChart() {
        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }
    }

    renderChart() {
        const data = this.props.data;
        if (!data || !data.labels || !data.labels.length) return;
        const el = this.canvasRef.el;
        if (!el) return;
        const ctx = el.getContext("2d");

        const isDark = el.closest(".adp-dark") !== null;
        const textColor = isDark ? "#cbd5e1" : "#475569";
        const gridColor = isDark ? "rgba(148,163,184,.12)" : "rgba(0,0,0,.06)";

        // Build floating bars for waterfall
        const values = data.values || [];
        const types = data.types || [];
        let running = 0;
        const barData = [];
        const bgColors = [];
        const borderColors = [];

        for (let i = 0; i < values.length; i++) {
            const v = values[i];
            if (types[i] === 'total') {
                barData.push([0, v]);
                bgColors.push(isDark ? "rgba(56,189,248,.75)" : "rgba(14,165,233,.65)");
                borderColors.push("#0ea5e9");
                running = v;
            } else if (types[i] === 'increase') {
                barData.push([running, running + v]);
                bgColors.push(isDark ? "rgba(34,197,94,.75)" : "rgba(22,163,74,.65)");
                borderColors.push("#22c55e");
                running += v;
            } else {
                // decrease — v is already negative
                barData.push([running + v, running]);
                bgColors.push(isDark ? "rgba(248,113,113,.75)" : "rgba(239,68,68,.65)");
                borderColors.push("#f87171");
                running += v;
            }
        }

        this.chart = new Chart(ctx, {
            type: "bar",
            data: {
                labels: data.labels,
                datasets: [{
                    data: barData,
                    backgroundColor: bgColors,
                    borderColor: borderColors,
                    borderWidth: 1,
                    borderRadius: 4,
                    barPercentage: 0.55,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: isDark ? "#1e293b" : "#fff",
                        titleColor: textColor,
                        bodyColor: textColor,
                        borderColor: gridColor,
                        borderWidth: 1,
                        callbacks: {
                            label: (c) => {
                                const [lo, hi] = c.raw;
                                return this.props.formatCurrency(hi - lo);
                            },
                        },
                    },
                },
                scales: {
                    x: { ticks: { color: textColor, font: { weight: "bold" } }, grid: { display: false } },
                    y: { ticks: { color: textColor, callback: (v) => this.props.formatCurrency(v) }, grid: { color: gridColor } },
                },
            },
        });
    }
}
