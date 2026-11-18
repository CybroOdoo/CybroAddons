import { Component, onMounted, proxy, signal } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

const { DateTime } = luxon;

const PALETTE = [
    "#003f5c", "#2f4b7c", "#f95d6a", "#665191", "#d45087",
    "#ff7c43", "#ffa600", "#a05195", "#6d5c16", "#CCCCFF",
];
const SINGLE_COLOR = "#003f5c";

// Server method called for each period of the "Top Moving Products" filter.
const TOP_PRODUCT_METHODS = {
    top_last_10_days: "top_products_last_ten",
    top_last_30_days: "top_products_last_thirty",
    top_last_3_month: "top_products_last_three_months",
    top_last_year: "top_products_last_year",
};
// Server method called for each period of the "Stock Moves By Location" filter.
const STOCK_MOVE_METHODS = {
    last_10_days: "stock_move_last_ten_days",
    this_month: "this_month",
    last_3_month: "last_three_month",
    last_year: "last_year",
};

/**
 * Builds the Chart.js configuration shared by all the dashboard graphs.
 *
 * @param {string} type chart type: bar, line, pie or doughnut.
 * @param {string[]} labels labels of the data points.
 * @param {number[]} data values of the data points.
 * @param {string} label name of the dataset.
 * @param {boolean} multicolor use one color per data point.
 */
function chartConfig(type, labels, data, label, multicolor) {
    const color = multicolor ? PALETTE : SINGLE_COLOR;
    const dataset = {
        label,
        data,
        backgroundColor: color,
        borderColor: color,
        borderWidth: 1,
    };
    const options = { responsive: true, maintainAspectRatio: false };
    if (type === "bar") {
        Object.assign(dataset, {
            barPercentage: 0.5,
            barThickness: 6,
            maxBarThickness: 8,
        });
    }
    if (type === "bar" || type === "line") {
        options.scales = { y: { beginAtZero: true } };
    }
    return { type, data: { labels, datasets: [dataset] }, options };
}

/** Zips two parallel lists into an object, keeping the display order. */
function toDict(keys, values) {
    const result = {};
    keys.forEach((key, index) => {
        result[key] = values[index];
    });
    return result;
}

/** Dashboard of the Inventory app: tiles, graphs and tables. */
class Dashboard extends Component {
    static template = "inventory_stock_dashboard_odoo.Dashboard";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.rootRef = signal.ref();
        // Chart.js instances, kept to destroy them before redrawing.
        this.charts = {};
        this.state = proxy({
            countDictionary: {},
            op_types: [],
            operations: [],
            colors: [],
            late_status: [],
            waiting_status: [],
            backorder_status: [],
            MoveData: {},
            operationDict: {},
            category: [],
            categoryId: [],
            categoryNames: [],
            categoryCounts: [],
            location_data: [],
            monthly_stock: [],
            monthly_stock_count: [],
            out_stock: [],
            out_stock_count: [],
            dead_stock_name: [],
            dead_stock_count: [],
        });
        onMounted(() => this.render_graphs());
    }

    // Helpers

    queryRoot(selector) {
        return this.rootRef().querySelector(selector);
    }

    drawChart(key, canvasSelector, type, labels, data, label, multicolor) {
        if (this.charts[key]) {
            this.charts[key].destroy();
        }
        this.charts[key] = new Chart(
            this.queryRoot(canvasSelector),
            chartConfig(type, labels, data, label, multicolor)
        );
    }

    toggle(selector) {
        const element = this.queryRoot(selector);
        element.style.display = element.style.display === "none" ? "block" : "none";
    }

    hide(selector) {
        this.queryRoot(selector).style.display = "none";
    }

    render_graphs() {
        this.render_operation_tile();
        this.render_top_product_bar_graph();
        this.render_stock_moves();
        this.render_product_moves();
        this.render_product_category();
        this.render_storage_location();
        this.render_out_of_stock_graph();
        this.render_dead_of_stock_graph();
    }

    // Renders the operation type tiles and graph.
    async render_operation_tile() {
        const result = await this.orm.call("stock.picking", "get_operation_types", []);
        const names = Object.values(result[3]);
        const counts = Object.values(result[0]);
        this.state.op_types = result[0];
        this.state.operations = result[3];
        this.state.colors = [
            "red", "blue", "green", "orange", "purple", "steel",
            "rebecca", "brown", "pink", "grey", "black",
        ];
        this.state.late_status = result[1];
        this.state.waiting_status = result[2];
        this.state.backorder_status = result[4];
        this.state.operationDict = toDict(names, counts);
        this.hide("#operation_type_table");
        this.drawChart("operation", "#operation", "bar", names, counts, _t("Count"), true);
    }

    // Renders the top moving products graph.
    async render_top_product_bar_graph() {
        await this.loadTopProducts("get_the_top_products");
    }

    async loadTopProducts(method) {
        const result = await this.orm.call("stock.move", method, []);
        this.state.countDictionary = toDict(result.products, result.count);
        this.hide("#pro_info");
        this.drawChart(
            "topProduct", "#canvaspie", "bar", result.products, result.count, _t("Count"), true
        );
    }

    // Renders the stock moves by location graph.
    async render_stock_moves() {
        // Same period as the filter selected by default.
        await this.loadStockMoves("stock_move_last_ten_days", ["last_10_days"]);
    }

    async loadStockMoves(method, args = []) {
        const result = await this.orm.call("stock.move", method, args);
        this.state.MoveData = toDict(result.name, result.count);
        this.hide("#stock_move_table");
        this.drawChart(
            "stockMoves", "#stock_moves", "pie", result.name, result.count, _t("Count"), true
        );
    }

    // Renders the product moves graph of the first category.
    async render_product_moves() {
        const result = await this.orm.call("stock.move.line", "get_product_moves", []);
        this.state.category = result.category_name;
        this.state.categoryId = result.category_id;
        if (this.state.categoryId.length) {
            await this.loadProductMoves(this.state.categoryId[0]);
        }
    }

    async loadProductMoves(categoryId) {
        const result = await this.orm.call(
            "stock.move.line", "product_move_by_category", [categoryId]
        );
        this.state.monthly_stock = result.name;
        this.state.monthly_stock_count = result.count;
        this.hide("#product_move_table");
        this.drawChart(
            "productMove", "#product_move_graph", "line",
            result.name, result.count, _t("Quantity Done"), false
        );
    }

    // Renders the product categories graph.
    async render_product_category() {
        const result = await this.orm.call("stock.picking", "get_product_category", []);
        this.state.categoryNames = result.name;
        this.state.categoryCounts = result.count;
        this.hide("#category_table");
        this.drawChart(
            "productCategory", "#product_category", "doughnut",
            result.name, result.count, _t("On-Hand Quantity"), true
        );
    }

    // Renders the on-hand quantity of each location.
    async render_storage_location() {
        this.state.location_data = await this.orm.call("stock.picking", "get_locations", []);
    }

    // Renders the dead stock graph.
    async render_dead_of_stock_graph() {
        const result = await this.orm.call("stock.move", "get_dead_of_stock", []);
        if (!result) {
            this.hide("#dead_stock");
            return;
        }
        this.queryRoot("#dead_stock").style.display = "block";
        this.state.dead_stock_name = result.product_name;
        this.state.dead_stock_count = result.total_quantity;
        this.hide("#dead_stock_table");
        this.drawChart(
            "deadStock", "#dead_stock_graph", "line",
            result.product_name, result.total_quantity, _t("Current Stock"), false
        );
    }

    // Renders the out-of-stock graph.
    async render_out_of_stock_graph() {
        const result = await this.orm.call("stock.quant", "get_out_of_stock", []);
        if (!result) {
            this.hide("#out_of_stock");
            return;
        }
        this.queryRoot("#out_of_stock").style.display = "block";
        this.state.out_stock = result.product_name;
        this.state.out_stock_count = result.total_quantity;
        this.hide("#out_of_stock_table");
        this.drawChart(
            "outOfStock", "#out_of_stock_graph", "bar",
            result.product_name, result.total_quantity, _t("Current Stock"), false
        );
    }

    // Details buttons of the graphs.
    onclick_top_product_info() {
        this.toggle("#pro_info");
    }

    onclick_stock_move_info() {
        this.toggle("#stock_move_table");
    }

    onclick_operation_type_info() {
        this.toggle("#operation_type_table");
    }

    onclick_product_category_info() {
        this.toggle("#category_table");
    }

    onclick_product_move_info() {
        this.toggle("#product_move_table");
    }

    onclick_out_of_stock_info() {
        this.toggle("#out_of_stock_table");
    }

    onclick_dead_stock_info() {
        this.toggle("#dead_stock_table");
    }

    // Period filters of the graphs.
    onchange_top_product_selection(ev) {
        const method = TOP_PRODUCT_METHODS[ev.currentTarget.value];
        if (method) {
            this.loadTopProducts(method);
        }
    }

    onchange_stock_moves_selection(ev) {
        const option = ev.currentTarget.value;
        const method = STOCK_MOVE_METHODS[option];
        if (method) {
            this.loadStockMoves(method, [option]);
        }
    }

    onchange_product_moves_selection(ev) {
        this.loadProductMoves(ev.currentTarget.value);
    }

    // Opens the transfers of an operation type.
    openTransfers(operationTypeKey, suffix, extraDomain = []) {
        // The keys of the server dictionaries are strings: use a real id.
        const operationTypeId = Number(operationTypeKey);
        const name = this.state.operations[operationTypeId];
        this.action.doAction({
            name: suffix ? `${name}/${suffix}` : name,
            type: "ir.actions.act_window",
            res_model: "stock.picking",
            views: [[false, "list"], [false, "form"]],
            domain: [["picking_type_id", "=", operationTypeId], ...extraDomain],
            target: "current",
        });
    }

    onclick_tiles(operationTypeId) {
        this.openTransfers(operationTypeId, "");
    }

    onclick_late_status(ev, operationTypeId) {
        ev.stopPropagation();
        // Same conditions as the late counter computed by the server.
        const now = DateTime.utc().toFormat("yyyy-MM-dd HH:mm:ss");
        this.openTransfers(operationTypeId, _t("Late"), [
            ["state", "in", ["assigned", "waiting", "confirmed"]],
            "|",
            "|",
            ["has_deadline_issue", "=", true],
            ["date_deadline", "<=", now],
            ["scheduled_date", "<=", now],
        ]);
    }

    onclick_waiting_status(ev, operationTypeId) {
        ev.stopPropagation();
        this.openTransfers(operationTypeId, _t("Waiting"), [["state", "=", "confirmed"]]);
    }

    onclick_backorders_status(ev, operationTypeId) {
        ev.stopPropagation();
        this.openTransfers(operationTypeId, _t("Backorders"), [["backorder_id", "!=", false]]);
    }
}

registry.category("actions").add("inventory_dashboard_tag", Dashboard);
