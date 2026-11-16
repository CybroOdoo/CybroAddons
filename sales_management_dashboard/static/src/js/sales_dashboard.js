/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import {
    Component,
    onMounted,
    onWillUnmount,
    proxy,
} from "@odoo/owl";


class SalesDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");

        this.charts = {};
        this.isMounted = false;

        this.state = proxy({
            data: {
                sales_by_team: [],
                sales_by_person: [],
                top_customers: [],
                top_products: [],
                lowest_products: [],
                overdue_customers: [],
                order_status: [],
                invoice_status: [],
                product_categories: [],
                sales_info: {
                    sale_orders: 0,
                    quotation: 0,
                    orders_to_invoice: 0,
                    orders_fully_invoiced: 0,
                    conversion_rate: 0,
                    total_revenue_mtd: 0,
                    total_revenue_ytd: 0,
                    avg_order_value: 0,
                },
                new_vs_returning: {
                    summary: {
                        labels: [],
                        values: [],
                    },
                    details: {
                        new: [],
                        returning: [],
                    },
                },
            },
            filters: this._getDefaultFilters(),
            loading: false,
        });

        onMounted(async () => {
            this.isMounted = true;
            await this._fetch_data();
        });

        onWillUnmount(() => {
            this.isMounted = false;
            this._destroyCharts();
        });
    }

    // ---------------------------------------------------------
    // DEFAULT FILTERS
    // ---------------------------------------------------------

    _getDefaultFilters() {
        return {
            global_filter: "select_period",
            custom_range: {
                from: null,
                to: null,
            },
            limit: 10,

            team_filter: "this_week",
            person_filter: "this_week",
            customer_filter: "this_week",
            product_filter: "this_week",
            low_product_filter: "this_week",
            order_filter: "this_week",
            invoice_filter: "this_week",
            overdue_filter: "this_week",
            nvrc_filter: "this_week",

            product_category_id: null,
            low_product_category_id: null,
        };
    }

    // ---------------------------------------------------------
    // FETCH DASHBOARD DATA
    // ---------------------------------------------------------

    async _fetch_data() {
        if (
            this.state.filters.global_filter === "custom" &&
            (
                !this.state.filters.custom_range.from ||
                !this.state.filters.custom_range.to
            )
        ) {
            return;
        }

        this.state.loading = true;

        try {
            const result = await this.orm.call(
                "sale.order",
                "get_sales_dashboard_data",
                [],
                {
                    filters: {
                        ...this.state.filters,
                        custom_range: {
                            ...this.state.filters.custom_range,
                        },
                    },
                }
            );

            if (!this.isMounted) {
                return;
            }

            this.state.data = {
                ...this.state.data,
                ...result,
            };

            this._render_charts();
        } catch (error) {
            console.error(
                "Failed to load Sales Dashboard data:",
                error
            );
        } finally {
            if (this.isMounted) {
                this.state.loading = false;
            }
        }
    }

    // ---------------------------------------------------------
    // CHART CLEANUP
    // ---------------------------------------------------------

    _destroyCharts() {
        Object.values(this.charts).forEach((chart) => {
            if (chart) {
                chart.destroy();
            }
        });

        this.charts = {};
    }

    // ---------------------------------------------------------
    // NAVIGATION
    // ---------------------------------------------------------

    goToRecord(model, id) {
        if (!model || !id) {
            return;
        }

        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Record",
            res_model: model,
            res_id: id,
            views: [[false, "form"]],
            target: "current",
        });
    }

    async _openListAction(name, model, domain) {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name,
            res_model: model,
            domain,
            views: [
                [false, "list"],
                [false, "form"],
            ],
            target: "current",
        });
    }

    async _getTileDomain(baseDomain) {
        return this.orm.call(
            "sale.order",
            "get_tile_domain",
            [],
            {
                base_domain: baseDomain,
                filters: this.state.filters,
            }
        );
    }

    async viewOrders() {
        const domain = await this._getTileDomain([
            ["state", "in", ["sale", "done"]],
        ]);

        return this._openListAction(
            "Sale Orders",
            "sale.order",
            domain
        );
    }

    async viewQuotations() {
        const domain = await this._getTileDomain([
            ["state", "in", ["draft", "sent"]],
        ]);

        return this._openListAction(
            "Quotations",
            "sale.order",
            domain
        );
    }

    async viewToInvoiceOrders() {
        const domain = await this._getTileDomain([
            ["invoice_status", "=", "to invoice"],
        ]);

        return this._openListAction(
            "Orders to Invoice",
            "sale.order",
            domain
        );
    }

    async viewFullyInvoicedOrders() {
        const domain = await this._getTileDomain([
            ["invoice_status", "=", "invoiced"],
        ]);

        return this._openListAction(
            "Fully Invoiced Orders",
            "sale.order",
            domain
        );
    }

    // ---------------------------------------------------------
    // CHART RENDERING
    // ---------------------------------------------------------

    _render_charts() {
        const data = this.state.data;

        if (!data) {
            return;
        }

        if (typeof Chart === "undefined") {
            console.error(
                "Chart.js is not loaded. Add Chart.js to web.assets_backend."
            );
            return;
        }

        this._destroyCharts();

        const createPieChart = (
            canvasId,
            labels,
            values,
            colors,
            chartKey
        ) => {
            const canvas = document.getElementById(canvasId);

            if (!canvas) {
                return;
            }

            this.charts[chartKey] = new Chart(canvas, {
                type: "pie",
                data: {
                    labels,
                    datasets: [{
                        data: values,
                        backgroundColor: colors,
                    }],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: {
                            position: "bottom",
                        },
                    },
                },
            });
        };

        const createBarChart = (
            canvasId,
            labels,
            values,
            color,
            chartKey
        ) => {
            const canvas = document.getElementById(canvasId);

            if (!canvas) {
                return;
            }

            this.charts[chartKey] = new Chart(canvas, {
                type: "bar",
                data: {
                    labels,
                    datasets: [{
                        label: "Quantity",
                        data: values,
                        backgroundColor: color,
                    }],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    scales: {
                        y: {
                            beginAtZero: true,
                        },
                    },
                    plugins: {
                        legend: {
                            display: false,
                        },
                    },
                },
            });
        };

        // Sales by team
        const teams = data.sales_by_team || [];

        createPieChart(
            "salesByTeamChart",
            teams.map((item) => item.name),
            teams.map((item) => item.amount),
            [
                "#007bff",
                "#28a745",
                "#ffc107",
                "#dc3545",
                "#ff7e00",
            ],
            "team"
        );

        // Sales by salesperson
        const persons = data.sales_by_person || [];

        createPieChart(
            "salesByPersonChart",
            persons.map((item) => item.name),
            persons.map((item) => item.amount),
            [
                "#17a2b8",
                "#ffc107",
                "#6c757d",
                "#6610f2",
            ],
            "person"
        );

        // Top-selling products
        const topProducts = data.top_products || [];

        createBarChart(
            "topProductsChart",
            topProducts.map((item) => item.name),
            topProducts.map((item) => item.quantity || 0),
            "#28a745",
            "top_products"
        );

        // Least-selling products
        const lowestProducts = data.lowest_products || [];

        createBarChart(
            "lowestProductsChart",
            lowestProducts.map((item) => item.name),
            lowestProducts.map((item) => item.quantity || 0),
            "#dc3545",
            "lowest_products"
        );

        // Order status
        const orderStatus = data.order_status || [];

        createPieChart(
            "orderStatusChart",
            orderStatus.map((item) => item.status),
            orderStatus.map((item) => item.count),
            [
                "#6c757d",
                "#17a2b8",
                "#28a745",
                "#ffc107",
                "#dc3545",
            ],
            "order_status"
        );

        // Invoice status
        const invoiceStatus = data.invoice_status || [];

        createPieChart(
            "invoiceStatusChart",
            invoiceStatus.map((item) => item.status),
            invoiceStatus.map((item) => item.count),
            [
                "#343a40",
                "#28a745",
                "#ffc107",
            ],
            "invoice_status"
        );

        // Overdue customers
        const overdueCustomers = data.overdue_customers || [];

        const overdueCanvas = document.getElementById(
            "overdueCustomersChart"
        );

        if (overdueCanvas) {
            this.charts.overdue_customers = new Chart(
                overdueCanvas,
                {
                    type: "bar",
                    data: {
                        labels: overdueCustomers.map(
                            (item) => item.name
                        ),
                        datasets: [{
                            label: "Outstanding Amount",
                            data: overdueCustomers.map(
                                (item) => item.amount
                            ),
                            backgroundColor: overdueCustomers.map(
                                (item) => {
                                    if (item.amount > 10000) {
                                        return "red";
                                    }
                                    if (item.amount > 5000) {
                                        return "orange";
                                    }
                                    return "yellow";
                                }
                            ),
                        }],
                    },
                    options: {
                        responsive: true,
                        scales: {
                            y: {
                                beginAtZero: true,
                            },
                        },
                        plugins: {
                            legend: {
                                display: false,
                            },
                        },
                    },
                }
            );
        }

        // New vs returning customers
        const customerSummary =
            data.new_vs_returning?.summary || {};

        createPieChart(
            "newVsReturningChart",
            customerSummary.labels || [],
            customerSummary.values || [],
            [
                "#28a745",
                "#ffc107",
            ],
            "new_vs_returning"
        );
    }

    // ---------------------------------------------------------
    // GLOBAL FILTER
    // ---------------------------------------------------------

    onChangeGlobalFilter(ev) {
        const selectedFilter = ev.target.value;

        this.state.filters.global_filter = selectedFilter;

        if (selectedFilter === "select_period") {
            this.state.filters = this._getDefaultFilters();
            this._fetch_data();
            return;
        }

        if (selectedFilter !== "custom") {
            this.state.filters.custom_range = {
                from: null,
                to: null,
            };
        }

        this._fetch_data();
    }

    // ---------------------------------------------------------
    // CUSTOM DATE FILTER
    // ---------------------------------------------------------

    onChangeCustomFrom(ev) {
        this.state.filters.custom_range.from = ev.target.value;
        this._maybeFetchCustom();
    }

    onChangeCustomTo(ev) {
        this.state.filters.custom_range.to = ev.target.value;
        this._maybeFetchCustom();
    }

    _maybeFetchCustom() {
        const customRange = this.state.filters.custom_range;

        if (
            this.state.filters.global_filter === "custom" &&
            customRange.from &&
            customRange.to
        ) {
            this._fetch_data();
        }
    }

    // ---------------------------------------------------------
    // SECTION FILTERS
    // ---------------------------------------------------------

    onChangeTeamFilter(ev) {
        this.state.filters.team_filter = ev.target.value;
        this._fetch_data();
    }

    onChangePersonFilter(ev) {
        this.state.filters.person_filter = ev.target.value;
        this._fetch_data();
    }

    onChangeCustomerFilter(ev) {
        this.state.filters.customer_filter = ev.target.value;
        this._fetch_data();
    }

    onChangeOrderFilter(ev) {
        this.state.filters.order_filter = ev.target.value;
        this._fetch_data();
    }

    onChangeInvoiceFilter(ev) {
        this.state.filters.invoice_filter = ev.target.value;
        this._fetch_data();
    }

    onChangeProductFilter(ev) {
        this.state.filters.product_filter = ev.target.value;
        this._fetch_data();
    }

    onChangeProductCategory(ev) {
        const value = ev.target.value;

        this.state.filters.product_category_id = value
            ? parseInt(value, 10)
            : null;

        this._fetch_data();
    }

    onChangeLowProductFilter(ev) {
        this.state.filters.low_product_filter = ev.target.value;
        this._fetch_data();
    }

    onChangeLowProductCategory(ev) {
        const value = ev.target.value;

        this.state.filters.low_product_category_id = value
            ? parseInt(value, 10)
            : null;

        this._fetch_data();
    }

    onChangeOverdueFilter(ev) {
        this.state.filters.overdue_filter = ev.target.value;
        this._fetch_data();
    }

    onChangeNvRFilter(ev) {
        this.state.filters.nvrc_filter = ev.target.value;
        this._fetch_data();
    }

    // ---------------------------------------------------------
    // GLOBAL LIMIT
    // ---------------------------------------------------------

    onChangeGlobalLimit(ev) {
        this.state.filters.limit = parseInt(ev.target.value, 10) || 10;
        this._fetch_data();
    }
}

SalesDashboard.template =
    "sales_management_dashboard.SalesDashboardTemplate";

registry.category("actions").add(
    "sales_dashboard",
    SalesDashboard
);