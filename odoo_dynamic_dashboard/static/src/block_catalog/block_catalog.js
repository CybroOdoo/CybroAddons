import { _t } from "@web/core/l10n/translation";

/**
 * Catalog of the building blocks of a dashboard: how they are presented in the
 * palette, which options the configurator shows for them, and their defaults.
 *
 * - value: one aggregated figure (measure)
 * - grouped: aggregated per value of a group by (measure + group by)
 * - subGroupBy: "required" or "optional" second group by (one series per value)
 * - records: list of records (columns, order)
 * - view: embedded Odoo view
 * - static: no model at all
 */
export const BLOCK_CATEGORIES = [
    { id: "kpi", label: _t("Key Figures") },
    { id: "chart", label: _t("Charts") },
    { id: "table", label: _t("Tables & Views") },
    { id: "layout", label: _t("Layout") },
];

export const BLOCK_TYPES = [
    // key figures
    { type: "tile", category: "kpi", kind: "value", width: 3, icon: "tag",
      label: _t("KPI Tile"), help: _t("One key figure") },
    { type: "progress", category: "kpi", kind: "value", width: 4, icon: "percent", target: true,
      label: _t("Progress Bar"), help: _t("A figure against its target") },
    { type: "gauge", category: "kpi", kind: "value", width: 4, icon: "speed", target: true,
      label: _t("Gauge"), help: _t("Speedometer towards a target") },
    // charts
    { type: "bar", category: "chart", kind: "grouped", width: 6, icon: "bar_chart", subGroupBy: "optional",
      label: _t("Bar Chart"), help: _t("Compare categories") },
    { type: "hbar", category: "chart", kind: "grouped", width: 6, icon: "format_align_left", subGroupBy: "optional",
      label: _t("Horizontal Bars"), help: _t("Rankings with long labels") },
    { type: "stacked_bar", category: "chart", kind: "grouped", width: 6, icon: "stacks",
      subGroupBy: "required", label: _t("Stacked Bars"), help: _t("Totals split by a second field") },
    { type: "line", category: "chart", kind: "grouped", width: 6, icon: "show_chart", subGroupBy: "optional",
      dateFirst: true, label: _t("Line Chart"), help: _t("Follow a trend over time") },
    { type: "area", category: "chart", kind: "grouped", width: 6, icon: "area_chart", subGroupBy: "optional",
      dateFirst: true, label: _t("Area Chart"), help: _t("Volume over time") },
    { type: "pie", category: "chart", kind: "grouped", width: 4, icon: "pie_chart",
      label: _t("Pie Chart"), help: _t("Share of a total") },
    { type: "doughnut", category: "chart", kind: "grouped", width: 4, icon: "radio_button_unchecked",
      label: _t("Doughnut Chart"), help: _t("Share of a total") },
    { type: "polar", category: "chart", kind: "grouped", width: 4, icon: "center_focus_weak",
      label: _t("Polar Area"), help: _t("Compare a few categories") },
    { type: "radar", category: "chart", kind: "grouped", width: 4, icon: "graph_2", subGroupBy: "optional",
      label: _t("Radar Chart"), help: _t("Compare profiles") },
    // tables and views
    { type: "table", category: "table", kind: "grouped", width: 4, icon: "format_list_numbered",
      label: _t("Ranking Table"), help: _t("Top values as a ranking") },
    { type: "pivot", category: "table", kind: "grouped", width: 6, icon: "table", subGroupBy: "required",
      label: _t("Pivot Table"), help: _t("Cross two fields") },
    { type: "record_list", category: "table", kind: "records", width: 6, icon: "view_list",
      label: _t("Record List"), help: _t("Latest or top records") },
    { type: "view", category: "table", kind: "view", width: 12, icon: "open_in_browser",
      label: _t("Odoo View"), help: _t("Embed a list, kanban, graph...") },
    // layout
    { type: "text", category: "layout", kind: "static", width: 12, icon: "title",
      label: _t("Text"), help: _t("A title or a note") },
];

export const BLOCK_TYPES_BY_NAME = Object.fromEntries(BLOCK_TYPES.map((info) => [info.type, info]));

export const BLOCK_WIDTHS = [
    { value: 3, label: "¼" },
    { value: 4, label: "⅓" },
    { value: 6, label: "½" },
    { value: 8, label: "⅔" },
    { value: 12, label: _t("Full") },
];

export const BLOCK_COLORS = [
    "#714B67", "#017E84", "#2E7D32", "#E65100", "#C62828",
    "#1565C0", "#6A1B9A", "#F9A825", "#455A64", "#00838F",
];

// Material Symbols icons shipped with Odoo, see web/tooling/icons/icons_wishlist.txt
export const BLOCK_ICONS = [
    "tag", "payments", "attach_money", "euro", "shopping_cart", "sell",
    "receipt_long", "group", "person", "handshake", "local_shipping", "inventory_2",
    "factory", "storefront", "description", "mail", "calendar_today", "schedule",
    "task", "check_circle", "warning", "star", "trophy", "rocket_launch",
];

// options of a block sent to the server, see dynamic.dashboard.block._get_block_config
export const CONFIG_KEYS = [
    "id", "name", "block_type", "model", "domain", "aggregate", "measure", "group_by", "sub_group_by",
    "date_granularity", "group_limit", "width", "color", "icon", "target_value", "list_fields",
    "order_by", "order_desc", "view_mode", "text_content",
];

let nextUid = 1;

/**
 * Prepare a block coming from the server for the dashboard client action.
 */
export function prepareBlock(block, { customName = true } = {}) {
    return { ...block, uid: nextUid++, version: 0, customName };
}

/**
 * New block of the given type, as dropped from the palette.
 */
export function createBlock(blockType, { color = BLOCK_COLORS[0] } = {}) {
    const info = BLOCK_TYPES_BY_NAME[blockType];
    return prepareBlock(
        {
            id: false,
            name: info.kind === "static" ? _t("Title") : info.label,
            block_type: blockType,
            model: false,
            model_label: "",
            domain: "[]",
            aggregate: "count",
            measure: false,
            group_by: false,
            sub_group_by: false,
            date_granularity: "month",
            group_limit: 10,
            width: info.width,
            color,
            icon: info.icon,
            target_value: 0,
            list_fields: [],
            order_by: false,
            order_desc: true,
            view_mode: "list",
            text_content: "",
            error: false,
        },
        { customName: info.kind === "static" }
    );
}

/**
 * Configuration of a block as sent to the server. The name is left out while the
 * user did not change it, so that the server suggests one matching the options.
 */
export function getBlockConfig(block) {
    const config = Object.fromEntries(CONFIG_KEYS.map((key) => [key, block[key]]));
    if (!block.customName) {
        delete config.name;
    }
    return config;
}

/**
 * Return why the block cannot be saved yet, or false.
 */
export function getBlockIssue(block) {
    const info = BLOCK_TYPES_BY_NAME[block.block_type];
    if (info.kind === "static") {
        return false;
    }
    if (!block.model) {
        return _t("Choose the data to show");
    }
    if (info.kind === "value" || info.kind === "grouped") {
        if (block.aggregate !== "count" && !block.measure) {
            return _t("Choose the field to measure");
        }
    }
    if (info.kind === "grouped" && !block.group_by) {
        return _t("Choose how to group the data");
    }
    if (info.subGroupBy === "required" && !block.sub_group_by) {
        return _t("Choose the second field to group by");
    }
    return false;
}

function fillRows(blocks, perRow) {
    for (let index = 0; index < blocks.length; index += perRow) {
        const row = blocks.slice(index, index + perRow);
        for (const block of row) {
            block.width = 12 / row.length;
        }
    }
}

/**
 * Reorder the blocks and set their widths so that they form full, tidy rows: key
 * figures first, then the charts, the tables, and the embedded views. Text blocks
 * are kept in place, as headers of the sections they delimit.
 *
 * @param {Object[]} blocks
 * @returns {Object[]} the blocks in their new order (their width is updated in place)
 */
export function autoArrangeBlocks(blocks) {
    const sections = [[]];
    for (const block of blocks) {
        if (block.block_type === "text") {
            sections.push([block]);
        } else {
            sections.at(-1).push(block);
        }
    }
    const arranged = [];
    for (const section of sections) {
        const groups = { header: [], kpi: [], wideChart: [], smallChart: [], table: [], view: [] };
        for (const block of section) {
            const info = BLOCK_TYPES_BY_NAME[block.block_type];
            if (info.kind === "static") {
                groups.header.push(block);
            } else if (info.category === "kpi") {
                groups.kpi.push(block);
            } else if (info.category === "chart") {
                groups[["pie", "doughnut", "polar", "radar"].includes(block.block_type) ? "smallChart" : "wideChart"].push(block);
            } else if (info.kind === "view") {
                groups.view.push(block);
            } else {
                groups.table.push(block);
            }
        }
        fillRows(groups.header, 1);
        fillRows(groups.kpi, 4);
        fillRows(groups.wideChart, 2);
        fillRows(groups.smallChart, 3);
        fillRows(groups.table, 2);
        fillRows(groups.view, 1);
        arranged.push(
            ...groups.header,
            ...groups.kpi,
            ...groups.wideChart,
            ...groups.smallChart,
            ...groups.table,
            ...groups.view
        );
    }
    return arranged;
}
