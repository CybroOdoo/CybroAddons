/** @odoo-module **/
// Reporting graphs in the pharma petrol / aqua / gold palette.
//
// Odoo's graph view picks series colours from a hard-coded palette in
// @web/core/colors/colors (blue, red, teal, orange, purple, yellow), which
// cannot be changed from SCSS. This patch recolours the datasets after Odoo
// builds them. Only petrol teal, aqua teal and gold shades are used, for
// every series (pass / fail included), so reports stay in the theme.
import { patch } from "@web/core/utils/patch";
import { cookie } from "@web/core/browser/cookie";
import { DEFAULT_BG, getCustomColor, lightenColor, darkenColor } from "@web/core/colors/colors";
import { GraphRenderer } from "@web/views/graph/graph_renderer";

const DARK = cookie.get("color_scheme") === "dark";

const PALETTE_LIGHT = [
    "#0b4650", // petrol
    "#2a7f86", // aqua teal
    "#e6a23c", // gold
    "#7fc4c0", // light aqua
    "#1d5f69", // petrol 600
    "#c4861f", // deep gold
    "#a8d5cf", // teal tint
    "#072b33", // petrol 900
    "#f2c46d", // light gold
    "#3fa3a9", // bright aqua
];
// Petrol disappears on the dark canvas, so dark mode leads with aqua.
const PALETTE_DARK = [
    "#3fa3a9",
    "#e6a23c",
    "#7fc4c0",
    "#2a7f86",
    "#f2c46d",
    "#a8d5cf",
    "#1d8a94",
    "#c4861f",
    "#ddefec",
    "#5fb8bd",
];
const PALETTE = DARK ? PALETTE_DARK : PALETTE_LIGHT;
// Odoo's grey "No data" slice colour (graph_renderer.js NO_DATA_COLOR).
const NO_DATA_COLOR = getCustomColor(DARK ? "dark" : "light", DEFAULT_BG, "#3C3E4B");

function pharmaColor(index) {
    return PALETTE[index % PALETTE.length];
}

patch(GraphRenderer.prototype, {
    getBarChartData() {
        const data = super.getBarChartData(...arguments);
        data.datasets.forEach((dataset, index) => {
            if (dataset.type === "line") {
                return; // the line overlay keeps Odoo's own styling
            }
            dataset.backgroundColor = pharmaColor(index);
        });
        return data;
    },

    getLineChartData() {
        const data = super.getLineChartData(...arguments);
        data.datasets.forEach((dataset, index) => {
            const color = pharmaColor(index);
            dataset.borderColor = color;
            dataset.pointBackgroundColor = color;
            dataset.hoverBackgroundColor = color;
            dataset.backgroundColor = getCustomColor(
                DARK ? "dark" : "light",
                lightenColor(color, 0.5),
                darkenColor(color, 0.5)
            );
        });
        return data;
    },

    getPieChartData() {
        const data = super.getPieChartData(...arguments);
        for (const dataset of data.datasets) {
            if (!Array.isArray(dataset.backgroundColor)) {
                continue;
            }
            // Keep Odoo's grey "No data" slice; recolour the rest.
            dataset.backgroundColor = dataset.backgroundColor.map((color, index) =>
                color === NO_DATA_COLOR ? color : pharmaColor(index)
            );
            dataset.hoverBackgroundColor = dataset.backgroundColor;
        }
        return data;
    },

    getLegendOptions() {
        const options = super.getLegendOptions(...arguments);
        const generate = options.labels?.generateLabels;
        if (this.model.metaData.mode === "pie" && generate) {
            // The pie legend reads Odoo's palette directly; take the slice colours instead.
            options.labels.generateLabels = (chart) =>
                generate(chart).map((item) => {
                    const bg = chart.data.datasets[0]?.backgroundColor;
                    if (Array.isArray(bg) && bg[item.index]) {
                        item.fillStyle = bg[item.index];
                    }
                    return item;
                });
        }
        return options;
    },
});
