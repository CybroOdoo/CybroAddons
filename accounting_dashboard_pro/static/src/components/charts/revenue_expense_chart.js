/** @odoo-module **/

import { Component, useRef, onMounted, onWillUpdateProps, onWillUnmount, onWillStart } from "@odoo/owl";
import { loadBundle } from "@web/core/assets";

export class RevenueExpenseChart extends Component {
    static template = "accounting_dashboard_pro.RevenueExpenseChart";
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
        const ctx = canvas.getContext("2d");

        const isDark = document.querySelector('.adp-dark') !== null;
        const textColor = isDark ? '#94a3b8' : '#64748b';
        const gridColor = isDark ? 'rgba(148, 163, 184, 0.08)' : 'rgba(0, 0, 0, 0.06)';

        // Revenue gradient
        const rGrad = ctx.createLinearGradient(0, 0, 0, 280);
        rGrad.addColorStop(0, 'rgba(16, 185, 129, 0.3)');
        rGrad.addColorStop(1, 'rgba(16, 185, 129, 0.02)');

        // Expense gradient
        const eGrad = ctx.createLinearGradient(0, 0, 0, 280);
        eGrad.addColorStop(0, 'rgba(239, 68, 68, 0.3)');
        eGrad.addColorStop(1, 'rgba(239, 68, 68, 0.02)');

        const labels = this.props.data.labels.map((l) => {
            const parts = l.split('-');
            return parts.length === 2 ? ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][parseInt(parts[1]) - 1] : l;
        });

        this.chart = new Chart(canvas, {
            type: 'line',
            data: {
                labels,
                datasets: [
                    {
                        label: 'Revenue',
                        data: this.props.data.revenue,
                        borderColor: '#10b981',
                        backgroundColor: rGrad,
                        fill: true,
                        tension: 0.4,
                        pointRadius: 3,
                        pointBackgroundColor: '#10b981',
                        borderWidth: 2,
                    },
                    {
                        label: 'Expenses',
                        data: this.props.data.expenses,
                        borderColor: '#ef4444',
                        backgroundColor: eGrad,
                        fill: true,
                        tension: 0.4,
                        pointRadius: 3,
                        pointBackgroundColor: '#ef4444',
                        borderWidth: 2,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: {
                            color: textColor,
                            font: { size: 12, weight: 600 },
                            usePointStyle: true,
                            pointStyleWidth: 10,
                            padding: 16,
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
                            label: (ctx) => `${ctx.dataset.label}: ${this.props.formatCurrency(ctx.raw)}`,
                        },
                    },
                },
                scales: {
                    x: {
                        grid: { color: gridColor },
                        ticks: { color: textColor, font: { size: 11 } },
                    },
                    y: {
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
                },
            },
        });
    }
}
