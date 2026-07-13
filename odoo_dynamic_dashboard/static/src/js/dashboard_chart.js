/** @odoo-module **/
import { registry } from '@web/core/registry';
import { Component, onWillStart, useState, useRef, onMounted, useEffect } from '@odoo/owl';
import { useService, useBus } from '@web/core/utils/hooks';
import { user } from "@web/core/user";
import { DashboardCardButtons } from './dashboard_card_buttons';
import { loadJS } from "@web/core/assets";

export class DashboardChart extends Component {
    setup() {
        this.action = useService("action");
        this.orm = useService('orm');
        this.chartContainer = useRef('ChartContainer');
        this.chartCanvas = useRef('ChartCanvas');
        this.chartElement = useRef('eChart');
        this.state = useState({
            colors: [],
            hasData: true,
        });

        onWillStart(async () => {
            await loadJS("/odoo_dynamic_dashboard/static/src/lib/chart.js/dist/chart.umd.min.js")
            await loadJS("/odoo_dynamic_dashboard/static/src/lib/chartjs-plugin-datalabels/dist/chartjs-plugin-datalabels.min.js");
            await loadJS("/odoo_dynamic_dashboard/static/src/lib/echarts/dist/echarts.min.js");
            await this.UpdateColor()
        });

        onMounted(() => this.renderChart());
        useEffect(() => { this.UpdateChart() }, () => [...Object.values(this.props.card)])
        useEffect(() => {
            if (this.state.hasData) {
                this.renderChart();
            }
        }, () => [this.state.hasData]);
    }

    async UpdateChart() {
        await this.UpdateColor();
        this.renderChart();
    }

    async UpdateColor() {
        var id = this.props.card.color_group_id.id ? this.props.card.color_group_id.id : this.props.card.color_group_id[0];
        this.state.colors = await this.orm.call(
            'dashboard.color.group',
            "get_colors",
            [id]
        );
    }

    getChartJsLegend() {
        const card = this.props.card;
        return {
            display: card.legend !== undefined ? card.legend : true,
            position: card.legend_position || 'bottom',
            align: card.legend_alignment || 'start',
            labels: {
                usePointStyle: true,
                pointStyle: card.legend_label_pointstyle || 'circle',
            }
        };
    }

    getEchartsLegend() {
        const card = this.props.card;
        const legendPos = card.legend_position || 'bottom';
        const legendAlign = card.legend_alignment || 'start';

        let legendConfig = {
            show: card.legend !== undefined ? card.legend : true,
        };

        if (legendPos === 'top') {
            legendConfig.top = 'top';
            legendConfig.left = legendAlign === 'start' ? 'left' : (legendAlign === 'end' ? 'right' : 'center');
        } else if (legendPos === 'bottom') {
            legendConfig.bottom = 'bottom';
            legendConfig.left = legendAlign === 'start' ? 'left' : (legendAlign === 'end' ? 'right' : 'center');
        } else if (legendPos === 'left') {
            legendConfig.left = 'left';
            legendConfig.top = legendAlign === 'start' ? 'top' : (legendAlign === 'end' ? 'bottom' : 'middle');
            legendConfig.orient = 'vertical';
        } else if (legendPos === 'right') {
            legendConfig.right = 'right';
            legendConfig.top = legendAlign === 'start' ? 'top' : (legendAlign === 'end' ? 'bottom' : 'middle');
            legendConfig.orient = 'vertical';
        }
        return legendConfig;
    }

    renderChart() {
        if (this.chart) { this.chart.destroy(); }
        if (this.chartInstance) { this.chartInstance.dispose(); }

        const card = this.props.card;
        const chartType = card.chart_type;

        let xData, yData, formattedEchartsData;
        try {
            xData = JSON.parse(card.chart_x_axis_data || "[]");
            yData = JSON.parse(card.chart_y_axis_data || "[]");
            formattedEchartsData = xData.map((name, index) => ({
                name: name,
                value: yData[index] || 0
            }));
        } catch (e) {
            xData = []; yData = []; formattedEchartsData = [];
        }

        const hasEffectiveData = !(!xData.length || !yData.length || xData.length !== yData.length || yData.every(v => v === 0));

        if (!hasEffectiveData) {
            this.state.hasData = false;
            return;
        }

        if (!this.state.hasData) {
            this.state.hasData = true;
            return;
        }

        Chart.register(Chart.Colors);

        // 1. BAR CHART (Dynamic)
        if (chartType == 'bar') {
            if (!this.chartCanvas.el) return;
            const ctx = this.chartCanvas.el.getContext("2d");
            var datas = {
                type: "bar",
                data: {
                    labels: xData,
                    datasets: [{
                        label: card.name,
                        data: yData,
                        backgroundColor: this.state.colors,
                        borderRadius: 5,
                    }],
                },
                plugins: [ChartDataLabels],
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    indexAxis: card.index_axis || 'x',
                    plugins: {
                        legend: this.getChartJsLegend(),
                        datalabels: {
                            color: 'white',
                            anchor: 'end',
                            align: 'start',
                            formatter: (v) => v >= 1000 ? (v / 1000).toFixed(1) + 'k' : v
                        }
                    }
                }
            };
            this.chart = new Chart(ctx, datas);
        }

        // 2. LINE & AREA CHART
        else if (chartType === 'line' || chartType === 'area') {
            if (!this.chartCanvas.el) return;
            const ctx = this.chartCanvas.el.getContext("2d");
            const isArea = chartType === 'area';
            let bgColor = 'transparent';
            if (isArea) {
                const gradient = ctx.createLinearGradient(0, 0, 0, 400);
                gradient.addColorStop(0, this.hexToRgba(card.chart_color || '#71639e', 0.5));
                gradient.addColorStop(1, this.hexToRgba(card.chart_color || '#71639e', 0.05));
                bgColor = gradient;
            }

            this.chart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: xData,
                    datasets: [{
                        label: card.name,
                        data: yData,
                        fill: isArea,
                        borderColor: card.chart_color || '#71639e',
                        backgroundColor: bgColor,
                        borderWidth: 3,
                        pointRadius: 5,
                        tension: 0.4,
                        spanGaps: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: this.getChartJsLegend(),
                        datalabels: { display: true, align: 'top' }
                    }
                }
            });
        }

        // 3. DOUGHNUT CHART
        else if (chartType == 'doughnut') {
            if (!this.chartCanvas.el) return;
            const ctx = this.chartCanvas.el.getContext("2d");
            this.chart = new Chart(ctx, {
                type: "doughnut",
                data: {
                    labels: xData,
                    datasets: [{
                        data: yData,
                        backgroundColor: this.state.colors,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '50%',
                    rotation: card.semi_circular ? -90 : 0,
                    circumference: card.semi_circular ? 180 : 360,
                    plugins: {
                        legend: this.getChartJsLegend()
                    }
                }
            });
        }

        // 4. PIE CHART
        else if (chartType == 'pie') {
            if (!this.chartCanvas.el) return;
            const ctx = this.chartCanvas.el.getContext("2d");
            this.chart = new Chart(ctx, {
                type: "pie",
                data: {
                    labels: xData,
                    datasets: [{
                        data: yData,
                        backgroundColor: this.state.colors,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    rotation: card.semi_circular ? -90 : 0,
                    circumference: card.semi_circular ? 180 : 360,
                    plugins: {
                        legend: this.getChartJsLegend()
                    }
                }
            });
        }

        // 5. RADIAL BAR CHART
        else if (chartType === 'radial') {
            if (this.chartElement.el) {
                this.chartInstance = echarts.init(this.chartElement.el);
                const radialSeries = xData.map((name, index) => {
                    const seriesData = Array(xData.length).fill(null);
                    seriesData[index] = yData[index];
                    return {
                        name: name,
                        type: 'bar',
                        data: seriesData,
                        coordinateSystem: 'polar',
                        stack: 'radial-stack',
                        label: { show: true, position: 'middle', formatter: '{b}' }
                    };
                });
                this.chartInstance.setOption({
                    color: this.state.colors,
                    legend: this.getEchartsLegend(),
                    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
                    polar: { radius: [20, '70%'], center: ['50%', '55%'] },
                    angleAxis: { max: Math.max(...yData) * 1.2, startAngle: 90 },
                    radiusAxis: { type: 'category', data: xData },
                    series: radialSeries
                });
            }
        }

        // 6. RADAR
        else if (chartType === 'radar') {
            if (!this.chartCanvas.el) return;
            const ctx = this.chartCanvas.el.getContext("2d");
            this.chart = new Chart(ctx, {
                type: 'radar',
                data: {
                    labels: xData,
                    datasets: [{
                        label: card.name,
                        data: yData,
                        backgroundColor: this.hexToRgba(card.chart_color, 0.25),
                        borderColor: card.chart_color,
                        pointRadius: 5
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: this.getChartJsLegend()
                    }
                }
            });
        }

        // 7. POLAR AREA
        else if (chartType === 'polarArea') {
            if (!this.chartCanvas.el) return;
            const ctx = this.chartCanvas.el.getContext("2d");
            this.chart = new Chart(ctx, {
                type: 'polarArea',
                data: {
                    labels: xData,
                    datasets: [{
                        data: yData,
                        backgroundColor: this.state.colors.map(c => this.hexToRgba(c, 0.6))
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: this.getChartJsLegend()
                    }
                }
            });
        }

        // 8. FUNNEL
        else if (chartType === 'funnel') {
            if (this.chartElement.el) {
                this.chartInstance = echarts.init(this.chartElement.el);
                this.chartInstance.setOption({
                    color: this.state.colors,
                    legend: this.getEchartsLegend(),
                    series: [{
                        type: 'funnel',
                        left: '10%',
                        width: '80%',
                        data: formattedEchartsData
                    }]
                });
            }
        }

        // 9. SCATTER CHART
        else if (chartType === 'scatter') {
            if (!this.chartCanvas.el) return;
            const ctx = this.chartCanvas.el.getContext("2d");
            this.chart = new Chart(ctx, {
                type: 'scatter',
                data: {
                    datasets: [{
                        label: card.name,
                        data: yData.map((v, i) => ({ x: i, y: v })),
                        backgroundColor: card.chart_color
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: this.getChartJsLegend()
                    }
                }
            });
        }

        // 10. BUBBLE CHART
        else if (chartType === 'bubble') {
            if (!this.chartCanvas.el) return;
            const ctx = this.chartCanvas.el.getContext("2d");

            const maxValue = Math.max(...yData);

            const bubbleData = yData.map((value, index) => ({
                x: index + 1,
                y: (value / maxValue) * 100,
                r: Math.max((value / maxValue) * 40, 8)
            }));

            this.chart = new Chart(ctx, {
                type: 'bubble',
                data: {
                    datasets: [{
                        label: card.name,
                        data: bubbleData,
                        backgroundColor: this.state.colors,
                        borderColor: '#fff',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: {
                            title: { display: true, text: 'Category' },
                            ticks: {
                                callback: (val) => xData[val - 1] || val
                            }
                        },
                        y: {
                            title: { display: true, text: 'Value (%)' },
                            beginAtZero: true,
                            max: 100
                        }
                    },
                    plugins: {
                        legend: this.getChartJsLegend(),
                        tooltip: {
                            callbacks: {
                                label: (ctx) => {
                                    const realValue = yData[ctx.dataIndex];
                                    return `${xData[ctx.dataIndex]} : ${realValue}`;
                                }
                            }
                        }
                    }
                }
            });
        }


        // 11. FLOWER CHART
        else if (chartType === 'flower') {
            if (this.chartElement.el) {
                this.chartInstance = echarts.init(this.chartElement.el);
                this.chartInstance.setOption({
                    color: this.state.colors,
                    legend: this.getEchartsLegend(),
                    series: [{
                        type: 'pie',
                        radius: ['20%', '70%'],
                        center: ['40%', '50%'],
                        data: formattedEchartsData,
                        roseType: 'area',
                        label: { show: true, position: 'outside' }
                    }]
                });
            }
        }

        // Fallback (for any unhandled types - using ECharts pie as before)
        //        else {
        //            if (this.chartElement.el) {
        //                this.chartInstance = echarts.init(this.chartElement.el);
        //                this.chartInstance.setOption({
        //                    color: this.state.colors,
        //                    series: [{
        //                        type: 'pie',
        //                        radius: card.semi_circular ? ['0%', '100%'] : '70%',
        //                        center: card.semi_circular ? ['50%', '70%'] : ['50%', '50%'],
        //                        startAngle: card.semi_circular ? 180 : 90,
        //                        endAngle: card.semi_circular ? 360 : -90,
        //                        data: formattedEchartsData
        //                    }]
        //                });
        //            }
        //        }
        this.attachResizeObserver();
    }

    attachResizeObserver() {
        if (this.chartInstance && this.chartElement.el) {
            this.resizeObserver = new ResizeObserver(() => {
                if (this.chartInstance) { this.chartInstance.resize(); }
            });
            this.resizeObserver.observe(this.chartElement.el);
        }
    }

    hexToRgba(hex, alpha = 1) {
        if (!hex) return `rgba(0,0,0,${alpha})`;
        hex = hex.replace(/^#/, '');
        if (hex.length === 3) hex = hex.split('').map(char => char + char).join('');
        const r = parseInt(hex.substring(0, 2), 16);
        const g = parseInt(hex.substring(2, 4), 16);
        const b = parseInt(hex.substring(4, 6), 16);
        return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    }
}

DashboardChart.template = 'DashboardChartTemplate';
DashboardChart.components = { DashboardCardButtons };

