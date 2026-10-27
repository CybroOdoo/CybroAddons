/** @odoo-module **/
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { loadBundle } from "@web/core/assets";
import { Component, onMounted, onWillStart, useRef, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

const CHART_COLORS = [
    "rgba(255, 99, 132, 1)",
    "rgba(54, 162, 235, 1)",
    "rgba(75, 192, 192, 1)",
    "rgba(153, 102, 255, 1)",
    "rgba(10, 20, 30, 1)",
];

/**
 * Format a Date as the UTC "YYYY-MM-DD HH:mm:ss" string expected by the
 * server for datetime fields.
 */
function formatServerDatetime(date) {
    return date.toISOString().slice(0, 19).replace("T", " ");
}

export class PosDashboard extends Component {
    static template = "all_in_one_pos_kit.PosDashboard";

    /** Initialize the dashboard state, services and chart references */
    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.salesCanvas = useRef("salesCanvas");
        this.customerCanvas = useRef("customerCanvas");
        this.productCanvas = useRef("productCanvas");
        this.categoryCanvas = useRef("categoryCanvas");
        this.charts = {};
        this.state = useState({
            payment_details: [],
            top_salesperson: [],
            selling_product: [],
            total_sale: 0,
            total_order_count: 0,
            total_refund_count: 0,
            total_session: 0,
            today_refund_total: 0,
            today_sale: 0,
        });
        onWillStart(async () => {
            // Chart.js is shipped with Odoo, it is not bundled in this module
            await loadBundle("web.chartjs_lib");
            await this.fetchData();
        });
        onMounted(async () => {
            await Promise.all([
                this.renderTopCustomerGraph(),
                this.renderTopProductGraph(),
                this.renderProductCategoryGraph(),
                this.renderSalesGraph("pos_hourly_sales"),
            ]);
        });
    }

    /** Fetch the values shown in the tiles and in the tables */
    async fetchData() {
        const result = await this.orm.call("pos.order", "get_refund_details", []);
        this.state.total_sale = result.total_sale;
        this.state.total_order_count = result.total_order_count;
        this.state.total_refund_count = result.total_refund_count;
        this.state.total_session = result.total_session;
        this.state.today_refund_total = result.today_refund_total;
        this.state.today_sale = result.today_sale;
        const data = await this.orm.call("pos.order", "get_details", []);
        this.state.payment_details = data.payment_details;
        this.state.top_salesperson = data.salesperson;
        this.state.selling_product = data.selling_product;
    }

    /**
     * Open a list/form action of the given model.
     * @param {string} name title of the action
     * @param {string} resModel model to open
     * @param {Array} domain domain of the records to show
     */
    openRecords(name, resModel, domain = []) {
        return this.actionService.doAction({
            name,
            type: "ir.actions.act_window",
            res_model: resModel,
            views: [[false, "list"], [false, "form"]],
            domain,
            target: "current",
        });
    }

    /** @returns {string} the start of the current day (server format) */
    get todayStart() {
        const date = new Date();
        date.setHours(0, 0, 0, 0);
        return formatServerDatetime(date);
    }

    posOrderToday() {
        return this.openRecords(_t("Today Orders"), "pos.order", [
            ["date_order", ">=", this.todayStart],
        ]);
    }

    posOrder() {
        return this.openRecords(_t("Total Orders"), "pos.order");
    }

    posRefundOrders() {
        return this.openRecords(_t("Refund Orders"), "pos.order", [
            ["amount_total", "<", 0.0],
        ]);
    }

    posRefundTodayOrders() {
        return this.openRecords(_t("Today Refund Orders"), "pos.order", [
            ["amount_total", "<", 0.0],
            ["date_order", ">=", this.todayStart],
        ]);
    }

    posSession() {
        return this.openRecords(_t("Sessions"), "pos.session");
    }

    /**
     * Create (or replace) the chart drawn in a canvas.
     * @param {string} key identifier of the chart
     * @param {Ref} canvasRef reference of the canvas element
     * @param {Object} config Chart.js configuration
     */
    drawChart(key, canvasRef, config) {
        if (!canvasRef.el) {
            return;
        }
        this.charts[key]?.destroy();
        this.charts[key] = new Chart(canvasRef.el, config);
    }

    /** Render the sales bar chart for hourly / monthly / yearly sales */
    async renderSalesGraph(option) {
        const arrays = await this.orm.call("pos.order", "get_department", [option]);
        this.drawChart("sales", this.salesCanvas, {
            type: "bar",
            data: {
                labels: arrays[1],
                datasets: [{
                    label: arrays[2],
                    data: arrays[0],
                    backgroundColor: CHART_COLORS,
                    borderWidth: 1,
                }],
            },
            options: { responsive: true },
        });
    }

    onChangeSalesPeriod(ev) {
        if (ev.target.value) {
            return this.renderSalesGraph(ev.target.value);
        }
    }

    /** Render the top customers pie chart */
    async renderTopCustomerGraph() {
        const arrays = await this.orm.call("pos.order", "get_the_top_customer");
        this.drawChart("customer", this.customerCanvas, {
            type: "pie",
            data: {
                labels: arrays[1],
                datasets: [{ label: "", data: arrays[0], backgroundColor: CHART_COLORS }],
            },
            options: {
                responsive: true,
                plugins: { title: { display: true, text: _t("Top Customers") } },
            },
        });
    }

    /** Render the top selling products bar chart */
    async renderTopProductGraph() {
        const arrays = await this.orm.call("pos.order", "get_the_top_products");
        this.drawChart("product", this.productCanvas, {
            type: "bar",
            data: {
                labels: arrays[1],
                datasets: [{
                    label: _t("Quantity"),
                    data: arrays[0],
                    backgroundColor: CHART_COLORS,
                    borderWidth: 1,
                }],
            },
            options: {
                responsive: true,
                indexAxis: "y",
                plugins: { title: { display: true, text: _t("Top Products") } },
            },
        });
    }

    /** Render the top product categories bar chart */
    async renderProductCategoryGraph() {
        const arrays = await this.orm.call("pos.order", "get_the_top_categories");
        this.drawChart("category", this.categoryCanvas, {
            type: "bar",
            data: {
                labels: arrays[1],
                datasets: [{
                    label: _t("Quantity"),
                    data: arrays[0],
                    backgroundColor: CHART_COLORS,
                    borderWidth: 1,
                }],
            },
            options: {
                responsive: true,
                indexAxis: "y",
                plugins: {
                    title: { display: true, text: _t("Top Product Categories") },
                },
            },
        });
    }
}

registry.category("actions").add("pos_order_menu", PosDashboard);
