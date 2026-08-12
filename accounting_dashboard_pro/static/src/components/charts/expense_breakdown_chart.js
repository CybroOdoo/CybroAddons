/** @odoo-module **/

import { Component, useRef, onMounted, onWillUpdateProps, onWillUnmount, onWillStart } from "@odoo/owl";
import { loadBundle } from "@web/core/assets";

export class ExpenseBreakdownChart extends Component {
    static template = "accounting_dashboard_pro.ExpenseBreakdownChart";
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

        const palette = [
            "#818cf8", "#fb923c", "#22c55e", "#f87171", "#38bdf8",
            "#e879f9", "#facc15", "#34d399", "#a78bfa", "#f472b6",
        ];

        this.chart = new Chart(ctx, {
            type: "doughnut",
            data: {
                labels: data.labels,
                datasets: [{
                    data: data.amounts,
                    backgroundColor: palette.slice(0, data.labels.length),
                    borderWidth: 0,
                    hoverOffset: 6,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: "55%",
                plugins: {
                    legend: {
                        position: "right",
                        labels: { color: textColor, usePointStyle: true, padding: 10, font: { size: 11 } },
                    },
                    tooltip: {
                        backgroundColor: isDark ? "#1e293b" : "#fff",
                        titleColor: textColor,
                        bodyColor: textColor,
                        borderColor: isDark ? "rgba(148,163,184,.2)" : "rgba(0,0,0,.1)",
                        borderWidth: 1,
                        callbacks: { label: (c) => `${c.label}: ${this.props.formatCurrency(c.raw)}` },
                    },
                },
            },
        });
    }
}
