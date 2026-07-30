/** @odoo-module **/

import { Component, useRef, onMounted, onWillUpdateProps, onWillUnmount, onWillStart } from "@odoo/owl";
import { loadBundle } from "@web/core/assets";

export class TopExpensesChart extends Component {
    static template = "accounting_dashboard_pro.TopExpensesChart";
    static props = {
        data: { type: Object },
        formatCurrency: { type: Function },
    };

    setup() {
        this.chartRef = useRef("chartCanvas");
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
        const canvas = this.chartRef.el;
        if (!canvas || !this.props.data?.labels?.length) return;

        const isDark = document.querySelector('.adp-dark') !== null;
        const textColor = isDark ? '#94a3b8' : '#64748b';
        const gridColor = isDark ? 'rgba(148, 163, 184, 0.08)' : 'rgba(0, 0, 0, 0.06)';

        const colors = [
            '#6366f1', '#8b5cf6', '#ec4899', '#f97316', '#14b8a6',
            '#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#06b6d4',
        ];

        this.chart = new Chart(canvas, {
            type: 'bar',
            data: {
                labels: this.props.data.labels,
                datasets: [{
                    data: this.props.data.data,
                    backgroundColor: colors.slice(0, this.props.data.labels.length),
                    borderRadius: 6,
                    borderSkipped: false,
                    barThickness: 22,
                }],
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: isDark ? '#1e293b' : '#ffffff',
                        titleColor: isDark ? '#f1f5f9' : '#0f172a',
                        bodyColor: isDark ? '#94a3b8' : '#475569',
                        borderColor: isDark ? 'rgba(148, 163, 184, 0.15)' : '#e2e8f0',
                        borderWidth: 1,
                        padding: 10,
                        cornerRadius: 8,
                        callbacks: {
                            label: (ctx) => this.props.formatCurrency(ctx.raw),
                        },
                    },
                },
                scales: {
                    x: {
                        grid: { color: gridColor },
                        ticks: {
                            color: textColor,
                            font: { size: 11 },
                            callback: (val) => {
                                if (val >= 1e6) return (val / 1e6).toFixed(1) + 'M';
                                if (val >= 1e3) return (val / 1e3).toFixed(0) + 'K';
                                return val;
                            },
                        },
                    },
                    y: {
                        grid: { display: false },
                        ticks: {
                            color: textColor,
                            font: { size: 11 },
                        },
                    },
                },
            },
        });
    }
}
