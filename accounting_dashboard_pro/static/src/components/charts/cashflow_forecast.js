/** @odoo-module **/

import { Component, useRef, onMounted, onWillUpdateProps, onWillUnmount, onWillStart } from "@odoo/owl";
import { loadBundle } from "@web/core/assets";

export class CashflowForecast extends Component {
    static template = "accounting_dashboard_pro.CashflowForecast";
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

        // Sample weekly
        const step = 7;
        const labels = [];
        const data = [];
        for (let i = 0; i < this.props.data.labels.length; i += step) {
            labels.push(this.props.data.labels[i]);
            data.push(this.props.data.data[i]);
        }

        const grad = ctx.createLinearGradient(0, 0, 0, 280);
        grad.addColorStop(0, 'rgba(59, 130, 246, 0.3)');
        grad.addColorStop(1, 'rgba(59, 130, 246, 0.02)');

        this.chart = new Chart(canvas, {
            type: 'line',
            data: {
                labels: labels.map((l) => {
                    const d = new Date(l);
                    return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
                }),
                datasets: [{
                    label: 'Projected Balance',
                    data,
                    borderColor: '#3b82f6',
                    backgroundColor: grad,
                    fill: true,
                    tension: 0.3,
                    pointRadius: 2,
                    pointBackgroundColor: '#3b82f6',
                    borderWidth: 2,
                }],
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
                            label: (ctx) => `Balance: ${this.props.formatCurrency(ctx.raw)}`,
                        },
                    },
                },
                scales: {
                    x: {
                        grid: { color: gridColor },
                        ticks: { color: textColor, font: { size: 11 }, maxTicksLimit: 8 },
                    },
                    y: {
                        grid: { color: gridColor },
                        ticks: {
                            color: textColor,
                            font: { size: 11 },
                            callback: (val) => {
                                if (Math.abs(val) >= 1e6) return (val / 1e6).toFixed(1) + 'M';
                                if (Math.abs(val) >= 1e3) return (val / 1e3).toFixed(0) + 'K';
                                return val;
                            },
                        },
                    },
                },
            },
        });
    }
}
