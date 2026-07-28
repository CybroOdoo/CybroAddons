/** @odoo-module **/

import { Component, useRef, onMounted, onWillUpdateProps, onWillUnmount, onWillStart } from "@odoo/owl";
import { loadBundle } from "@web/core/assets";

export class IncomeExpensePie extends Component {
    static template = "accounting_dashboard_pro.IncomeExpensePie";
    static props = {
        revenue: { type: Number },
        expenses: { type: Number },
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
            this.destroyChart();
            this.props = next;
            this.renderChart();
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
        if (!canvas) return;

        const isDark = document.querySelector('.adp-dark') !== null;
        const revenue = this.props.revenue || 0;
        const expenses = this.props.expenses || 0;

        this.chart = new Chart(canvas, {
            type: 'doughnut',
            data: {
                labels: ['Revenue', 'Expenses'],
                datasets: [{
                    data: [revenue, expenses],
                    backgroundColor: [
                        'rgba(16, 185, 129, 0.85)',
                        'rgba(239, 68, 68, 0.85)',
                    ],
                    borderColor: [
                        '#10b981',
                        '#ef4444',
                    ],
                    borderWidth: 2,
                    hoverOffset: 8,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '65%',
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: isDark ? '#94a3b8' : '#475569',
                            font: { size: 12, weight: 600 },
                            padding: 16,
                            usePointStyle: true,
                            pointStyleWidth: 12,
                        },
                    },
                    tooltip: {
                        backgroundColor: isDark ? '#1e293b' : '#ffffff',
                        titleColor: isDark ? '#f1f5f9' : '#0f172a',
                        bodyColor: isDark ? '#94a3b8' : '#475569',
                        borderColor: isDark ? 'rgba(148, 163, 184, 0.15)' : '#e2e8f0',
                        borderWidth: 1,
                        padding: 10,
                        cornerRadius: 8,
                        callbacks: {
                            label: (ctx) => {
                                const total = revenue + expenses;
                                const pct = total > 0 ? ((ctx.raw / total) * 100).toFixed(1) : 0;
                                return `${ctx.label}: ${this.props.formatCurrency(ctx.raw)} (${pct}%)`;
                            },
                        },
                    },
                },
            },
        });
    }
}
