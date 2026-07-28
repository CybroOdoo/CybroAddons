/** @odoo-module **/

import { Component, useRef, onMounted, onWillUpdateProps, onWillUnmount, onWillStart } from "@odoo/owl";
import { loadBundle } from "@web/core/assets";

export class MonthlyCashflowBars extends Component {
    static template = "accounting_dashboard_pro.MonthlyCashflowBars";
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

        this.chart = new Chart(ctx, {
            type: "bar",
            data: {
                labels: data.labels,
                datasets: [
                    {
                        label: "Cash In",
                        data: data.inflows,
                        backgroundColor: isDark ? "rgba(34,197,94,.7)" : "rgba(22,163,74,.6)",
                        borderRadius: 4,
                        stack: "cashflow",
                    },
                    {
                        label: "Cash Out",
                        data: (data.outflows || []).map((v) => -v),
                        backgroundColor: isDark ? "rgba(248,113,113,.7)" : "rgba(239,68,68,.6)",
                        borderRadius: 4,
                        stack: "cashflow",
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { labels: { color: textColor, usePointStyle: true, padding: 16 } },
                    tooltip: {
                        backgroundColor: isDark ? "#1e293b" : "#fff",
                        titleColor: textColor,
                        bodyColor: textColor,
                        borderColor: gridColor,
                        borderWidth: 1,
                        callbacks: { label: (c) => `${c.dataset.label}: ${this.props.formatCurrency(Math.abs(c.raw))}` },
                    },
                },
                scales: {
                    x: { stacked: true, ticks: { color: textColor }, grid: { display: false } },
                    y: { stacked: true, ticks: { color: textColor, callback: (v) => this.props.formatCurrency(v) }, grid: { color: gridColor } },
                },
            },
        });
    }
}
