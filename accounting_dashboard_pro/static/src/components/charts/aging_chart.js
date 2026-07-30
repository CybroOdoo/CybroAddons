/** @odoo-module **/

import { Component, useRef, onMounted, onWillUpdateProps, onWillUnmount, onWillStart } from "@odoo/owl";
import { loadBundle } from "@web/core/assets";

export class AgingChart extends Component {
    static template = "accounting_dashboard_pro.AgingChart";
    static props = {
        receivableData: { type: Object },
        payableData: { type: Object },
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
        const textColor = isDark ? '#94a3b8' : '#64748b';
        const gridColor = isDark ? 'rgba(148, 163, 184, 0.08)' : 'rgba(0, 0, 0, 0.06)';

        const labels = this.props.receivableData?.labels || ['Current', '1-30', '31-60', '61-90', '90+'];
        const recData = this.props.receivableData?.data || [0, 0, 0, 0, 0];
        const payData = this.props.payableData?.data || [0, 0, 0, 0, 0];

        this.chart = new Chart(canvas, {
            type: 'bar',
            data: {
                labels,
                datasets: [
                    {
                        label: 'Receivable',
                        data: recData,
                        backgroundColor: 'rgba(59, 130, 246, 0.7)',
                        borderColor: '#3b82f6',
                        borderWidth: 1,
                        borderRadius: 4,
                    },
                    {
                        label: 'Payable',
                        data: payData,
                        backgroundColor: 'rgba(245, 158, 11, 0.7)',
                        borderColor: '#f59e0b',
                        borderWidth: 1,
                        borderRadius: 4,
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
