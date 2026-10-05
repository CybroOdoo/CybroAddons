import { cookie } from "@web/core/browser/cookie";
import { getColor, getCustomColor, hexToRGBA } from "@web/core/colors/colors";
import { useChart } from "@web/core/utils/chart_hook";
import { formatFloat } from "@web/views/fields/formatters";
import { View } from "@web/views/view";
import { Component, onError, proxy, t, useProps } from "@odoo/owl";
import { BLOCK_TYPES_BY_NAME, getBlockIssue } from "../block_catalog/block_catalog";

const colorScheme = cookie.get("color_scheme");
const LEGEND_COLOR = getCustomColor(colorScheme, "#111827", "#ffffff");
const GRID_COLOR = getCustomColor(colorScheme, "rgba(0,0,0,.1)", "rgba(255,255,255,.15)");
const EMPTY_COLOR = getCustomColor(colorScheme, "#e5e7eb", "#3c3e4b");

const CHART_TYPES = {
    bar: "bar",
    hbar: "bar",
    stacked_bar: "bar",
    line: "line",
    area: "line",
    pie: "pie",
    doughnut: "doughnut",
    polar: "polarArea",
    radar: "radar",
};
const CIRCULAR_TYPES = ["pie", "doughnut", "polar"];

export function formatBlockValue(value) {
    // keep small integers (counts) free of decimals, and shorten large numbers (12.5k)
    const decimals = Number.isInteger(value) && Math.abs(value) < 1000 ? 0 : 2;
    return formatFloat(value || 0, { humanReadable: true, decimals });
}

export function getProgress(block) {
    if (!block.target_value) {
        return 0;
    }
    return Math.round((100 * (block.value || 0)) / block.target_value);
}

export class DashboardChart extends Component {
    static template = "odoo_dynamic_dashboard.DashboardChart";
    props = useProps({
        block: t.object(),
        interactive: t.boolean(),
        onDrillDown: t.function(),
    });

    setup() {
        this.chart = useChart(() => this.getChartConfig());
    }

    getChartConfig() {
        const { block_type: blockType, labels, series, color } = this.props.block;
        const isCircular = CIRCULAR_TYPES.includes(blockType);
        const isMultiSeries = series.length > 1;
        const datasets = series.map((serie, index) => {
            const serieColor = isMultiSeries ? getColor(index, colorScheme, series.length) : color;
            const dataset = {
                label: serie.label,
                data: serie.values,
                backgroundColor: serieColor,
                borderColor: serieColor,
            };
            if (isCircular) {
                dataset.backgroundColor = labels.map((_, labelIndex) =>
                    getColor(labelIndex, colorScheme, labels.length)
                );
                dataset.borderColor = getCustomColor(colorScheme, "#ffffff", "#262a36");
            } else if (blockType === "area" || blockType === "radar") {
                dataset.backgroundColor = hexToRGBA(serieColor, 0.25);
                dataset.fill = true;
            }
            if (blockType === "line" || blockType === "area") {
                dataset.tension = 0.3;
                dataset.pointRadius = 3;
            }
            if (blockType === "bar" || blockType === "hbar" || blockType === "stacked_bar") {
                dataset.borderRadius = 4;
                dataset.maxBarThickness = 48;
            }
            return dataset;
        });
        const hasOnlyIntegers = series.every((serie) => serie.values.every(Number.isInteger));
        const valueAxis = {
            beginAtZero: true,
            stacked: blockType === "stacked_bar",
            ticks: {
                color: LEGEND_COLOR,
                // no 0.5 steps on an axis of counts
                precision: hasOnlyIntegers ? 0 : undefined,
                callback: (value) => formatBlockValue(value),
            },
            grid: { color: GRID_COLOR },
        };
        const labelAxis = {
            stacked: blockType === "stacked_bar",
            ticks: { color: LEGEND_COLOR },
            grid: { display: false },
        };
        let scales = {};
        if (blockType === "radar" || blockType === "polar") {
            scales = { r: { beginAtZero: true, ticks: { display: false }, grid: { color: GRID_COLOR } } };
        } else if (!isCircular) {
            scales = blockType === "hbar" ? { x: valueAxis, y: labelAxis } : { x: labelAxis, y: valueAxis };
        }
        const options = {
            maintainAspectRatio: false,
            animation: false,
            indexAxis: blockType === "hbar" ? "y" : "x",
            onClick: (ev, elements) => {
                if (elements.length) {
                    const { datasetIndex, index } = elements[0];
                    const serie = series[datasetIndex];
                    const label = isMultiSeries ? `${labels[index]} / ${serie.label}` : labels[index];
                    this.props.onDrillDown({ label, domain: serie.domains[index] });
                }
            },
            onHover: (ev, elements) => {
                ev.native.target.style.cursor = elements.length ? "pointer" : "default";
            },
            plugins: {
                legend: {
                    display: isCircular || isMultiSeries,
                    position: "bottom",
                    labels: { color: LEGEND_COLOR, boxWidth: 12 },
                },
                tooltip: {
                    callbacks: {
                        label: (item) => `${item.dataset.label}: ${formatBlockValue(item.raw)}`,
                    },
                },
            },
            scales,
        };
        if (!this.props.interactive) {
            // in the builder a click selects the block
            options.events = [];
        }
        return { type: CHART_TYPES[blockType], data: { labels, datasets }, options };
    }
}

export class DashboardGauge extends Component {
    static template = "odoo_dynamic_dashboard.DashboardGauge";
    props = useProps({ block: t.object() });

    setup() {
        this.chart = useChart(() => this.getChartConfig());
    }

    getProgress() {
        return getProgress(this.props.block);
    }

    formatValue(value) {
        return formatBlockValue(value);
    }

    getChartConfig() {
        const { value, target_value: target, color } = this.props.block;
        const reached = Math.min(value || 0, target || 0);
        return {
            type: "doughnut",
            data: {
                datasets: [
                    {
                        data: target ? [reached, Math.max(target - reached, 0)] : [0, 1],
                        backgroundColor: [color, EMPTY_COLOR],
                        borderWidth: 0,
                    },
                ],
            },
            options: {
                maintainAspectRatio: false,
                animation: false,
                rotation: -90,
                circumference: 180,
                cutout: "72%",
                events: [],
                plugins: { legend: { display: false }, tooltip: { enabled: false } },
            },
        };
    }
}

/**
 * Odoo view (list, kanban...) embedded in a block. A view failing to load (no view
 * of this type for the model, missing rights...) only breaks its own block.
 */
export class DashboardView extends Component {
    static template = "odoo_dynamic_dashboard.DashboardView";
    static components = { View };
    props = useProps({
        block: t.object(),
        onOpenRecord: t.function(),
    });

    setup() {
        this.state = proxy({ error: false });
        onError((error) => {
            this.state.error = error.message || String(error);
        });
        const { model, view_mode: viewMode, record_domain: domain } = this.props.block;
        this.viewProps = {
            resModel: model,
            type: viewMode,
            domain: domain || [],
            context: {},
            display: { controlPanel: false, searchPanel: false },
            views: [
                [false, viewMode],
                [false, "search"],
            ],
            selectRecord: (resId) => this.props.onOpenRecord(model, resId),
        };
        if (viewMode === "list") {
            this.viewProps.allowSelectors = false;
        }
    }
}

export class DashboardBlock extends Component {
    static template = "odoo_dynamic_dashboard.DashboardBlock";
    static components = { DashboardChart, DashboardGauge, DashboardView };
    props = useProps({
        block: t.object(),
        editMode: t.boolean(),
        selected: t.boolean(),
        onSelect: t.function(),
        onDuplicate: t.function(),
        onDelete: t.function(),
        onDrillDown: t.function(),
        onOpenRecord: t.function(),
        filterCount: t.number().optional(0),
        filterSummary: t.string().optional(""),
        onFilter: t.function().optional(),
        onAnalyze: t.function().optional(),
    });

    getInfo() {
        return BLOCK_TYPES_BY_NAME[this.props.block.block_type];
    }

    getIssue() {
        return getBlockIssue(this.props.block);
    }

    /**
     * Whether the data of the block is still being computed: its configuration is
     * complete but its preview did not come back yet.
     */
    isLoading() {
        const { block } = this.props;
        switch (this.getInfo().kind) {
            case "value":
                return block.value === undefined;
            case "grouped":
                return !Array.isArray(block.series) || !Array.isArray(block.labels);
            case "records":
                return !Array.isArray(block.rows);
            case "view":
                return block.record_domain === undefined;
            default:
                return false;
        }
    }

    isChart() {
        return this.props.block.block_type in CHART_TYPES;
    }

    hasNoData() {
        const { labels, rows } = this.props.block;
        return Boolean((labels && !labels.length) || (rows && !rows.length));
    }

    getProgress() {
        return getProgress(this.props.block);
    }

    getProgressWidth() {
        return Math.max(0, Math.min(this.getProgress(), 100));
    }

    formatValue(value) {
        return formatBlockValue(value);
    }

    getPivotTotal(labelIndex) {
        return this.props.block.series.reduce((total, serie) => total + serie.values[labelIndex], 0);
    }

    getTextParagraphs() {
        return (this.props.block.text_content || "").split(/\n+/).filter(Boolean);
    }

    onClick(ev) {
        if (this.props.editMode) {
            ev.stopPropagation();
            this.props.onSelect();
        }
    }

    drillDown(group) {
        if (!this.props.editMode) {
            this.props.onDrillDown(group);
        }
    }

    drillDownAll() {
        const { block } = this.props;
        this.drillDown({ label: block.name, domain: block.record_domain });
    }

    openRecord(resId) {
        if (!this.props.editMode) {
            this.props.onOpenRecord(this.props.block.model, resId);
        }
    }
}
