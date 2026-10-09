import { Component, t, useProps } from "@odoo/owl";
import { formatCurrency } from "@web/core/currency";
import { _t } from "@web/core/l10n/translation";
import { useChart } from "@web/core/utils/chart_hook";
import { useService } from "@web/core/utils/hooks";
import { getColor, hexToRGBA } from "@web/core/colors/colors";
import { cookie } from "@web/core/browser/cookie";
import { humanNumber } from "@web/core/utils/numbers";
import { formatFloat, formatInteger } from "@web/views/fields/formatters";

/** Format one cell value according to its column type. */
export function formatCell(value, type, currencyId) {
    if (value === null || value === undefined || value === "") {
        return "";
    }
    switch (type) {
        case "monetary":
            return formatCurrency(value, currencyId);
        case "number":
            return Number.isInteger(value) ? formatInteger(value) : formatFloat(value);
        case "percent":
            return `${formatFloat(value, { digits: [16, 1] })} %`;
        default:
            return String(value);
    }
}

/**
 * Chart values: company currency by default, ``value_type`` "usd" for AI
 * costs (often fractions of a cent) or "number" for counts such as tokens.
 */
export function formatChartValue(value, block, compact = false) {
    switch (block.value_type) {
        case "number":
            return compact ? humanNumber(value) : formatInteger(value);
        case "usd": {
            const size = Math.abs(value);
            const digits = size === 0 || size >= 100 ? 0 : size >= 1 ? 2 : size >= 0.01 ? 3 : 4;
            return `$${formatFloat(value, { digits: [16, compact ? Math.min(digits, 3) : Math.max(digits, 2)] })}`;
        }
        default:
            return compact
                ? formatCurrency(value, block.currency_id, { humanReadable: true, digits: [16, 0] })
                : formatCurrency(value, block.currency_id);
    }
}

export class AiTableBlock extends Component {
    static template = "ai_accounting_analytics.TableBlock";
    props = useProps({
        block: t.object(),
        onExport: t.function().optional(),
        onOpenRecord: t.function().optional(),
    });

    cell(value, column) {
        return formatCell(value, column.type, this.props.block.currency_id);
    }

    isNumeric(column) {
        return ["monetary", "number", "percent"].includes(column.type);
    }

    rowClass(row) {
        const classes = [];
        if (row.bold) {
            classes.push("fw-bold");
        }
        if (row.res_id) {
            classes.push("o_ai_accounting_row_link");
        }
        return classes.join(" ");
    }

    indent(row, index) {
        return index === 0 && row.level ? `padding-left: ${0.5 + row.level}rem` : "";
    }

    onRowClick(row) {
        if (row.res_id && this.props.onOpenRecord) {
            this.props.onOpenRecord(row.res_model, row.res_id);
        }
    }

    exportCsv() {
        const block = this.props.block;
        const escape = (value) => `"${String(value ?? "").replace(/"/g, '""')}"`;
        const lines = [block.columns.map((column) => escape(column.label)).join(",")];
        for (const row of block.rows) {
            lines.push(row.cells.map(escape).join(","));
        }
        const blob = new Blob([lines.join("\n")], { type: "text/csv;charset=utf-8" });
        const link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.download = `${(block.title || "table").replace(/[^\w\- ]+/g, "")}.csv`;
        link.click();
        URL.revokeObjectURL(link.href);
    }
}

export class AiChartBlock extends Component {
    static template = "ai_accounting_analytics.ChartBlock";
    props = useProps({ block: t.object() });

    ui = useService("ui");
    chart = useChart(() => this.getChartConfig());

    getChartConfig() {
        const block = this.props.block;
        // Pies are drawn as doughnuts, lines as soft filled areas.
        const isPie = block.chart_type === "pie";
        const isLine = block.chart_type === "line";
        const colorScheme = cookie.get("color_scheme");
        const size = isPie ? block.labels.length : block.datasets.length;
        const gridColor = colorScheme === "dark" ? "rgba(255,255,255,.08)" : "rgba(0,0,0,.06)";
        // Brand colours exposed by chat.scss; a single series uses them as a gradient.
        const styles = getComputedStyle(this.chart.ref() || document.body);
        const brandStart = styles.getPropertyValue("--o-ai-accounting-start").trim() || getColor(0, colorScheme, 1);
        const brandEnd = styles.getPropertyValue("--o-ai-accounting-end").trim() || brandStart;
        const single = !isPie && block.datasets.length === 1;
        const gradient = (alphaStart, alphaEnd) => (context) => {
            const { ctx, chartArea } = context.chart;
            if (!chartArea) {
                return brandStart;
            }
            const fill = ctx.createLinearGradient(0, chartArea.bottom, 0, chartArea.top);
            fill.addColorStop(0, hexToRGBA(brandEnd, alphaStart));
            fill.addColorStop(1, hexToRGBA(brandStart, alphaEnd));
            return fill;
        };
        const datasets = block.datasets.map((dataset, index) => {
            const color = single ? brandStart : getColor(index, colorScheme, size);
            let background = color;
            if (isPie) {
                // Brand colour first, then clearly different colours.
                background = dataset.data.map((_value, i) =>
                    i === 0 ? brandStart : getColor(i, colorScheme, size)
                );
            } else if (single) {
                background = isLine ? gradient(0.02, 0.3) : gradient(0.85, 1);
            } else if (isLine) {
                background = hexToRGBA(color, 0.15);
            }
            return {
                label: dataset.label,
                data: dataset.data,
                backgroundColor: background,
                borderColor: isPie ? "transparent" : color,
                borderWidth: isLine ? 2.5 : 0,
                borderRadius: isPie || isLine ? 0 : 6,
                maxBarThickness: 40,
                hoverOffset: 6,
                pointRadius: isLine ? 3 : 0,
                pointHoverRadius: 5,
                tension: 0.35,
                fill: isLine,
            };
        });
        const money = (value) => formatChartValue(value, block);
        const compactMoney = (value) => formatChartValue(value, block, true);
        return {
            type: isPie ? "doughnut" : block.chart_type,
            data: { labels: block.labels, datasets },
            options: {
                maintainAspectRatio: false,
                cutout: isPie ? "62%" : undefined,
                interaction: { mode: "index", intersect: false },
                plugins: {
                    legend: {
                        display: isPie || datasets.length > 1,
                        // Beside a doughnut, below it on phones.
                        position: isPie ? (this.ui.isSmall ? "bottom" : "right") : "top",
                        labels: { usePointStyle: true, boxWidth: 8 },
                    },
                    tooltip: {
                        padding: 10,
                        cornerRadius: 8,
                        callbacks: {
                            label: (item) => ` ${item.dataset.label}: ${money(item.raw)}`,
                        },
                    },
                },
                scales: isPie
                    ? {}
                    : {
                          x: {
                              grid: { display: false },
                              border: { display: false },
                              ticks: { maxRotation: 0, autoSkip: true, autoSkipPadding: 12 },
                          },
                          y: {
                              grid: { color: gridColor },
                              border: { display: false },
                              ticks: { callback: (value) => compactMoney(value), maxTicksLimit: 6 },
                          },
                      },
            },
        };
    }
}

export class AiKpiBlock extends Component {
    static template = "ai_accounting_analytics.KpiBlock";
    props = useProps({
        block: t.object(),
        onOpenRecord: t.function().optional(),
    });

    value(item) {
        if (item.value === null || item.value === undefined) {
            return "—";
        }
        switch (item.type) {
            case "days":
                return _t("%s days", formatFloat(item.value, { digits: [16, 0] }));
            case "ratio":
                return formatFloat(item.value, { digits: [16, 2] });
            case "percent":
                return `${formatFloat(item.value, { digits: [16, 1] })} %`;
            case "number":
                return formatFloat(item.value, { digits: [16, 0] });
            default:
                return formatCurrency(item.value, this.props.block.currency_id);
        }
    }

    delta(item) {
        if (item.delta === null || item.delta === undefined) {
            return "";
        }
        const sign = item.delta > 0 ? "+" : "";
        return `${sign}${formatFloat(item.delta, { digits: [16, 1] })} %`;
    }

    openRecord() {
        const block = this.props.block;
        if (block.res_id && this.props.onOpenRecord) {
            this.props.onOpenRecord(block.res_model, block.res_id);
        }
    }
}
