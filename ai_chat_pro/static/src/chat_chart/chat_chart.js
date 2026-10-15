import { loadBundle } from "@web/core/assets";
import { cookie } from "@web/core/browser/cookie";
import { getColor, getCustomColor, hexToRGBA } from "@web/core/colors/colors";
import { Component, onWillStart, useEffect, useRef } from "@odoo/owl";

const CIRCULAR_TYPES = ["pie", "doughnut"];

/**
 * Chart of a table answer, drawn with Odoo's Chart.js bundle. The chart says which
 * column names the items (``label``) and which columns to draw (``values``); the
 * values come from the raw numbers of the rows, and tooltips show them formatted as
 * in the table.
 */
export class AiChatChart extends Component {
    static template = "ai_chat_pro.ChatChart";
    static props = {
        result: Object,
        type: String,
        onOpenRow: { type: Function, optional: true },
        // receives a function exporting the chart as a PNG image (a Blob)
        registerExport: { type: Function, optional: true },
    };

    setup() {
        this.chart = null;
        this.canvasRef = useRef("canvas");
        onWillStart(() => loadBundle("web.chartjs_lib"));
        useEffect(
            () => {
                this.chart = new Chart(this.canvasRef.el, this.getChartConfig());
                return () => {
                    this.chart.destroy();
                    this.chart = null;
                };
            },
            () => [this.props.result, this.props.type]
        );
        this.props.registerExport?.(() => this.exportImage());
    }

    /**
     * The chart as a PNG image, titled, on the background of the theme: the canvas
     * of Chart.js is transparent.
     *
     * @returns {Promise<Blob|null>}
     */
    exportImage() {
        const chart = this.chart;
        if (!chart) {
            return Promise.resolve(null);
        }
        const source = chart.canvas;
        const ratio = source.width / (source.clientWidth || source.width);
        const padding = 24 * ratio;
        const titleHeight = 36 * ratio;
        const canvas = document.createElement("canvas");
        canvas.width = source.width + 2 * padding;
        canvas.height = source.height + titleHeight + 2 * padding;
        const context = canvas.getContext("2d");
        const isDark = cookie.get("color_scheme") === "dark";
        context.fillStyle = isDark ? "#262a36" : "#ffffff";
        context.fillRect(0, 0, canvas.width, canvas.height);
        const fontFamily = getComputedStyle(document.body).fontFamily;
        context.fillStyle = isDark ? "#f1f3f5" : "#212529";
        context.font = `600 ${16 * ratio}px ${fontFamily}`;
        context.textBaseline = "top";
        context.fillText(this.props.result.heading || this.props.result.title || "", padding, padding);
        const tags = (this.props.result.tags || []).join(", ");
        if (tags) {
            context.fillStyle = isDark ? "#adb5bd" : "#6c757d";
            context.font = `400 ${12 * ratio}px ${fontFamily}`;
            context.fillText(tags, padding, padding + 20 * ratio);
        }
        context.drawImage(source, padding, padding + titleHeight);
        return new Promise((resolve) => canvas.toBlob(resolve, "image/png"));
    }

    get isCircular() {
        return CIRCULAR_TYPES.includes(this.props.type);
    }

    getChartConfig() {
        const { result, type } = this.props;
        const { chart, columns, rows } = result;
        const colorScheme = cookie.get("color_scheme");
        const valueIndexes = this.isCircular ? chart.values.slice(0, 1) : chart.values;
        const isHorizontal = type === "bar" && chart.horizontal;
        const datasets = valueIndexes.map((valueIndex, seriesIndex) => {
            const color = getColor(seriesIndex, colorScheme, "odoo");
            const dataset = {
                label: columns[valueIndex].label,
                data: rows.map((row) => row.raw[valueIndex] ?? 0),
                backgroundColor: color,
                borderColor: color,
                borderRadius: type === "bar" ? 4 : 0,
                maxBarThickness: 36,
                valueIndex,
            };
            if (this.isCircular) {
                dataset.backgroundColor = rows.map((_row, index) => getColor(index, colorScheme, rows.length));
                dataset.borderColor = getCustomColor(colorScheme, "#ffffff", "#262a36");
            } else if (type === "line") {
                dataset.backgroundColor = hexToRGBA(color, 0.15);
                dataset.fill = valueIndexes.length === 1;
                dataset.tension = 0.3;
                dataset.pointRadius = 3;
            }
            return dataset;
        });
        const gridColor = getCustomColor(colorScheme, "rgba(0,0,0,0.06)", "rgba(255,255,255,0.08)");
        return {
            type,
            data: { labels: rows.map((row) => row.cells[chart.label]), datasets },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: isHorizontal ? "y" : "x",
                animation: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? false : { duration: 250 },
                onClick: (_event, elements) => this.onClick(elements),
                onHover: (event, elements) => {
                    if (this.props.onOpenRow && event.native?.target) {
                        event.native.target.style.cursor = elements.length && this.canOpen(elements) ? "pointer" : "default";
                    }
                },
                plugins: {
                    legend: {
                        display: this.isCircular || valueIndexes.length > 1,
                        position: this.isCircular ? "right" : "bottom",
                        labels: { boxWidth: 12, usePointStyle: true },
                    },
                    tooltip: {
                        callbacks: {
                            // the value as formatted in the table (amounts with their currency...)
                            label: (context) => {
                                const row = rows[context.dataIndex];
                                return `${context.dataset.label}: ${row.cells[context.dataset.valueIndex]}`;
                            },
                        },
                    },
                },
                scales: this.isCircular
                    ? {}
                    : {
                          x: { grid: { display: isHorizontal, color: gridColor }, ticks: { autoSkip: true } },
                          y: { grid: { display: !isHorizontal, color: gridColor }, beginAtZero: true },
                      },
            },
        };
    }

    canOpen(elements) {
        const row = this.props.result.rows[elements[0].index];
        return Boolean(this.props.result.openable && row?.id);
    }

    onClick(elements) {
        if (elements.length && this.canOpen(elements)) {
            this.props.onOpenRow?.(this.props.result.rows[elements[0].index]);
        }
    }
}
