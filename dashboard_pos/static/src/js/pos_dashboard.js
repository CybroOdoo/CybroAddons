import { Component, onMounted, onWillStart, onWillUnmount, proxy, signal } from "@odoo/owl";
import { loadBundle } from "@web/core/assets";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

const PALETTE = [
    "#213843", "#468D8B", "#74B3A8", "#F6DAC0", "#FEAF76",
    "#DA6D58", "#213843", "#468D8B", "#74B3A8", "#DA6D58",
];

export class PosDashboard extends Component {
    static template = "PosDashboard";

    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.charts = {};
        // Domains sent by the server, so the lists match the tiles.
        this.domains = {};
        // Refs of the canvases the charts are drawn on.
        this.salesCanvas = signal(null);
        this.customersCanvas = signal(null);
        this.productsCanvas = signal(null);
        this.categoriesCanvas = signal(null);
        this.state = proxy({
            payment_details: [],
            top_salesperson: [],
            sessions: [],
            total_sale: "0.00",
            total_order_count: 0,
            total_refund_count: 0,
            total_session: 0,
            today_refund_total: 0,
            today_sale: 0,
        });
        onWillStart(async () => {
            await Promise.all([loadBundle("web.chartjs_lib"), this.fetchData()]);
        });
        onMounted(async () => {
            await Promise.all([
                this.renderTopCustomerGraph(),
                this.renderTopProductGraph(),
                this.renderProductCategoryGraph(),
                this.renderSalesGraph("pos_hourly_sales"),
            ]);
        });
        onWillUnmount(() => {
            Object.values(this.charts).forEach((chart) => chart.destroy());
        });
    }

    /** Fetch the data of the tiles and of the tables. */
    async fetchData() {
        const [summary, details] = await Promise.all([
            this.orm.call("pos.order", "get_refund_details", []),
            this.orm.call("pos.order", "get_details", []),
        ]);
        this.domains = {
            order: summary.order_domain,
            refund: summary.refund_domain,
            today: summary.today_domain,
            session: summary.session_domain,
        };
        Object.assign(this.state, {
            total_sale: summary.total_sale,
            total_order_count: summary.total_order_count,
            total_refund_count: summary.total_refund_count,
            total_session: summary.total_session,
            today_refund_total: summary.today_refund_total,
            today_sale: summary.today_sale,
            payment_details: details.payment_details,
            top_salesperson: details.salesperson,
            sessions: details.sessions,
        });
    }

    /** Open a list of records in the main area. */
    openList(name, resModel, domain = []) {
        return this.actionService.doAction({
            name,
            type: "ir.actions.act_window",
            res_model: resModel,
            views: [[false, "list"], [false, "form"]],
            domain,
            target: "current",
        });
    }

    openTodayOrders() {
        return this.openList(_t("Today Orders"), "pos.order", [
            ...this.domains.order,
            ...this.domains.today,
        ]);
    }

    openAllOrders() {
        return this.openList(_t("Total Orders"), "pos.order", this.domains.order);
    }

    openRefundOrders() {
        return this.openList(_t("Total Refund Orders"), "pos.order", [
            ...this.domains.order,
            ...this.domains.refund,
        ]);
    }

    openRefundTodayOrders() {
        return this.openList(_t("Today Refund Orders"), "pos.order", [
            ...this.domains.order,
            ...this.domains.refund,
            ...this.domains.today,
        ]);
    }

    openSessions() {
        return this.openList(_t("Sessions"), "pos.session", this.domains.session);
    }

    /** Draw (or redraw) the chart ``key`` on the canvas held by ``canvasRef``. */
    drawChart(key, canvasRef, type, labels, values, datasetLabel, title, indexAxis = "x") {
        const canvas = canvasRef();
        if (!canvas) {
            return;
        }
        if (this.charts[key]) {
            this.charts[key].destroy();
        }
        const colors = values.map((value, index) => PALETTE[index % PALETTE.length]);
        this.charts[key] = new window.Chart(canvas, {
            type,
            data: {
                labels,
                datasets: [{
                    label: datasetLabel,
                    data: values,
                    backgroundColor: colors,
                    borderColor: colors,
                    borderWidth: 1,
                }],
            },
            options: {
                responsive: true,
                indexAxis,
                plugins: {
                    legend: { display: true, position: "bottom" },
                    title: { display: true, text: title },
                },
            },
        });
    }

    onSalesPeriodChange(ev) {
        return this.renderSalesGraph(ev.target.value);
    }

    async renderSalesGraph(option) {
        const [values, labels, groupName] = await this.orm.call(
            "pos.order", "get_department", [option]
        );
        this.drawChart(
            "sales", this.salesCanvas, "bar", labels, values, groupName, _t("Sale Details")
        );
    }

    async renderTopCustomerGraph() {
        const [values, labels] = await this.orm.call("pos.order", "get_the_top_customer", []);
        this.drawChart(
            "customers", this.customersCanvas, "pie",
            labels, values, "", _t("Top Customers")
        );
    }

    async renderTopProductGraph() {
        const [values, labels] = await this.orm.call("pos.order", "get_the_top_products", []);
        this.drawChart(
            "products", this.productsCanvas, "bar",
            labels, values, _t("Quantity"), _t("Top Products"), "y"
        );
    }

    async renderProductCategoryGraph() {
        const [values, labels] = await this.orm.call("pos.order", "get_the_top_categories", []);
        this.drawChart(
            "categories", this.categoriesCanvas, "bar",
            labels, values, _t("Quantity"), _t("Top Categories"), "y"
        );
    }
}

registry.category("actions").add("pos_order_menu", PosDashboard);
