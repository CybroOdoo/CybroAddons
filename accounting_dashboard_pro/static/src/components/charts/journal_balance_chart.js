/** @odoo-module **/

import { Component, useRef, onMounted, onWillUnmount, onWillStart, useState } from "@odoo/owl";
import { loadBundle } from "@web/core/assets";

export class JournalBalanceChart extends Component {
    static template = "accounting_dashboard_pro.JournalBalanceChart";
    static props = { journals: { type: Array }, formatCurrency: Function };

    setup() {
        this.canvasRef = useRef("canvas");
        this.chart = null;
        this.state = useState({ selectedIndex: 0 });
        onWillStart(async () => {
            await loadBundle("web.chartjs_lib");
        });
        onMounted(() => this.renderChart());
        onWillUnmount(() => this.destroyChart());
    }

    get selectedJournal() {
        return this.props.journals[this.state.selectedIndex] || null;
    }

    selectJournal(idx) {
        this.state.selectedIndex = idx;
        this.destroyChart();
        this.renderChart();
    }

    destroyChart() {
        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }
    }

    renderChart() {
        const data = this.selectedJournal;
        if (!data || !data.labels || !data.labels.length) return;
        const el = this.canvasRef.el;
        if (!el) return;
        const ctx = el.getContext("2d");

        const isDark = el.closest(".adp-dark") !== null;
        const textColor = isDark ? "#cbd5e1" : "#475569";
        const gridColor = isDark ? "rgba(148,163,184,.12)" : "rgba(0,0,0,.06)";
        const isBank = data.journal_type === "bank";
        const lineColor = isBank ? "#0ea5e9" : "#22c55e";

        const gradient = ctx.createLinearGradient(0, 0, 0, el.height);
        gradient.addColorStop(0, isBank ? "rgba(14,165,233,.25)" : "rgba(34,197,94,.25)");
        gradient.addColorStop(1, "rgba(0,0,0,0)");

        this.chart = new Chart(ctx, {
            type: "line",
            data: {
                labels: data.labels,
                datasets: [{
                    label: "Balance",
                    data: data.balances,
                    borderColor: lineColor,
                    backgroundColor: gradient,
                    fill: true,
                    tension: 0.35,
                    pointRadius: 3,
                    pointHoverRadius: 5,
                    pointBackgroundColor: lineColor,
                    borderWidth: 2,
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
                            label: (c) => `Balance: ${this.props.formatCurrency(c.raw)}`,
                        },
                    },
                },
                scales: {
                    x: { ticks: { color: textColor, maxRotation: 45, font: { size: 10 } }, grid: { display: false } },
                    y: { ticks: { color: textColor, callback: (v) => this.props.formatCurrency(v) }, grid: { color: gridColor } },
                },
            },
        });
    }
}
