/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { GraphRenderer } from "@web/views/graph/graph_renderer";

patch(GraphRenderer.prototype, {
    getScaleOptions() {
        const options = super.getScaleOptions(...arguments);
        const darkTextColor = "#1F2937"; // Dark slate for maximum legibility on light graph canvas
        if (options.x && options.x.ticks) {
            options.x.ticks.color = darkTextColor;
            options.x.ticks.font = { weight: "600", size: 12 };
        }
        if (options.y && options.y.ticks) {
            options.y.ticks.color = darkTextColor;
            options.y.ticks.font = { weight: "600", size: 12 };
        }
        return options;
    },
    getLegendOptions() {
        const options = super.getLegendOptions(...arguments);
        const darkTextColor = "#1F2937";
        if (options && options.labels) {
            options.labels.color = darkTextColor;
            options.labels.font = { weight: "600", size: 12 };
            if (typeof options.labels.generateLabels === "function") {
                const originalGenerateLabels = options.labels.generateLabels;
                options.labels.generateLabels = (chart) => {
                    const labels = originalGenerateLabels(chart);
                    return labels.map((label) => ({
                        ...label,
                        fontColor: darkTextColor,
                        color: darkTextColor,
                    }));
                };
            }
        }
        return options;
    }
});
