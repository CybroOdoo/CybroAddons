/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { GraphRenderer } from "@web/views/graph/graph_renderer";

/**
 * Helper to dynamically determine text color from DOM context
 * instead of forcing a hardcoded color everywhere.
 */
function getContextualColor(el) {
    if (typeof window !== "undefined") {
        const target = el
            || (typeof document !== "undefined" && document.querySelector(".o_graph_renderer"))
            || (typeof document !== "undefined" && document.body);
        if (target) {
            const style = window.getComputedStyle(target);
            const color = style?.color;
            if (color && color !== "rgba(0, 0, 0, 0)" && color !== "transparent") {
                return color;
            }
        }
    }
    return null;
}

function getRendererElement(renderer) {
    if (typeof renderer.containerRef === "function") {
        return renderer.containerRef();
    }
    if (renderer.containerRef?.el) {
        return renderer.containerRef.el;
    }
    if (typeof renderer.rootRef === "function") {
        return renderer.rootRef();
    }
    if (renderer.rootRef?.el) {
        return renderer.rootRef.el;
    }
    return null;
}

patch(GraphRenderer.prototype, {
    getScaleOptions() {
        const options = super.getScaleOptions();
        const el = getRendererElement(this);
        const fontColor = getContextualColor(el);

        if (fontColor) {
            if (options.x?.ticks) {
                options.x.ticks.color = fontColor;
            }
            if (options.x?.title) {
                options.x.title.color = fontColor;
            }

            if (options.y?.ticks) {
                options.y.ticks.color = fontColor;
            }
            if (options.y?.title) {
                options.y.title.color = fontColor;
            }
        }

        return options;
    },

    getLegendOptions() {
        const options = super.getLegendOptions();
        const el = getRendererElement(this);
        const defaultColor = getContextualColor(el);

        if (options.labels?.generateLabels && defaultColor) {
            const originalGenerateLabels = options.labels.generateLabels;

            options.labels.generateLabels = (chart) => {
                const color = getContextualColor(chart?.canvas) || defaultColor;
                return originalGenerateLabels(chart).map((label) => ({
                    ...label,
                    fontColor: color || label.fontColor,
                }));
            };
        }

        return options;
    },
});

