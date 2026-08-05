/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onMounted } from "@odoo/owl";

const actionRegistry = registry.category("actions");


class SalesDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.actionService = useService('action')
        this.charts = {};
        this.state = useState({
             data: {
                sales_info: {
                    sale_orders: 0,
                    quotation: 0,
                    orders_to_invoice: 0,
                    orders_fully_invoiced: 0,
                }
             },
            filters: {
                global_filter: "select_period",
                custom_range: { from: null, to: null },
                limit: "10",
                team_filter: "this_week",
                person_filter: "this_week",
                product_filter: "this_week",
                low_product_filter: "this_week",
                customer_filter: "this_week",
                order_filter: "this_week",
                invoice_filter: "this_week",
            },
        });
        onMounted(() => this._fetch_data());
    }

    async _fetch_data() {
    const result = await this.orm.call(
        "sale.order",
        "get_sales_dashboard_data",
        [],
        { filters: this.state.filters }
    );

    this.state.data = result;
    this._render_charts();
    }


    goToRecord(model, id) {
        window.location.href = `/web#model=${model}&id=${id}&view_type=form`;
    }
    async viewOrders(){
    const domain = await this.orm.call(
        "sale.order",
        "get_tile_domain",
        [],
        {
            base_domain: [['state', 'in', ['sale', 'done']]],
            filters: this.state.filters
        }
    );

    this.actionService.doAction({
        type: "ir.actions.act_window",
        name: "Sale Orders",
        res_model: "sale.order",
        domain,
        views: [[false, "list"], [false, "form"]]
    })
    }

    async viewQuotations(){
        const domain = await this.orm.call(
            "sale.order",
            "get_tile_domain",
            [],
            {
                base_domain: [['state', 'in', ['draft','sent']]],
                filters: this.state.filters
            }
        );

        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Quotations",
            res_model: "sale.order",
            domain,
            views: [[false, "list"], [false, "form"]]
        })
    }

    async viewToInvoiceOrders(){
        const domain = await this.orm.call(
            "sale.order",
            "get_tile_domain",
            [],
            {
                base_domain: [['invoice_status', '=', 'to invoice']],
                filters: this.state.filters
            }
        );

        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "To Invoice",
            res_model: "sale.order",
            domain,
            views: [[false, "list"], [false, "form"]]
        })
    }

    async viewFullyInvoicedOrders(){
        const domain = await this.orm.call(
            "sale.order",
            "get_tile_domain",
            [],
            {
                base_domain: [['invoice_status', '=', 'invoiced']],
                filters: this.state.filters
            }
        );

        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Fully Invoiced",
            res_model: "sale.order",
            domain,
            views: [[false, "list"], [false, "form"]]
        })
    }

    _render_charts() {
        const d = this.state.data;
        if (!d.sales_by_team) return;
        Object.values(this.charts).forEach(chart => chart?.destroy());
        this.charts = {};

        const pie = (id, labels, data, bg, chartKey) => {
            const ctx = document.getElementById(id);
            if (!ctx) return;
            this.charts[chartKey] = new Chart(ctx, {
                type: "pie",
                data: {
                    labels,
                    datasets: [{ data, backgroundColor: bg }],
                },
                options: {
                    responsive: true,
                    plugins: { legend: { position: 'bottom' } }
                }
            });
        };
        const bar = (id, labels, data, bg, chartKey) => {
            const ctx = document.getElementById(id);
            if (!ctx) return;
            this.charts[chartKey] = new Chart(ctx, {
                type: "bar",
                data: {
                    labels,
                    datasets: [{ label: "", data, backgroundColor: bg }],
                },
                options: {
                    responsive: true,
                    scales: { y: { beginAtZero: true } },
                    plugins: { legend: { display: false } }
                }
            });
        };

        pie("salesByTeamChart",
            d.sales_by_team.map(x => x.name),
            d.sales_by_team.map(x => x.amount),
            ["#007bff", "#28a745", "#ffc107", "#dc3545", "#ff7e00"],
            "team");

        pie("salesByPersonChart",
            d.sales_by_person.map(x => x.name),
            d.sales_by_person.map(x => x.amount),
            ["#17a2b8", "#ffc107", "#6c757d", "#6610f2"],
            "person");

        bar("topProductsChart",
            d.top_products.map(x => x.name),
            d.top_products.map(x => x.qty),
            "#28a745",
            "top_products");

        bar("lowestProductsChart",
            d.lowest_products.map(x => x.name),
            d.lowest_products.map(x => x.qty),
            "#dc3545",
            "lowest_products");

        pie("orderStatusChart",
            d.order_status.map(x => x.status),
            d.order_status.map(x => x.count),
            ["#6c757d", "#17a2b8", "#28a745", "#ffc107"],
            "order_status");

        pie("invoiceStatusChart",
            d.invoice_status.map(x => x.status),
            d.invoice_status.map(x => x.count),
            ["#343a40", "#28a745", "#ffc107"],
            "invoice_status");

        bar(
            "overdueCustomersChart",
            d.overdue_customers.map(x => x.name),
            d.overdue_customers.map(x => x.amount),
            d.overdue_customers.map(x =>
                x.amount > 10000 ? "red" :
                x.amount > 5000 ? "orange" :
                "yellow"),
            "overdue_customers");

        pie("newVsReturningChart",
            d.new_vs_returning.summary.labels,
            d.new_vs_returning.summary.values,
            ["#28a745", "#ffc107"],
            "new_vs_returning");
    }

    onChangeGlobalFilter(ev) {
    this.state.filters.global_filter = ev.target.value;

    if (this.state.filters.global_filter === "select_period") {
        this.state.filters = {
            global_filter: "select_period",
            custom_range: { from: null, to: null },
            limit: "10",
            team_filter: "this_week",
            person_filter: "this_week",
            product_filter: "this_week",
            low_product_filter: "this_week",
            customer_filter: "this_week",
            order_filter: "this_week",
            invoice_filter: "this_week",
            overdue_filter: "this_week",
            nvrc_filter: "this_week",
        };

        this.render();
        this._fetch_data();
        return;
    }

    if (this.state.filters.global_filter !== "custom") {
        this.state.filters.custom_range = { from: null, to: null };
    }

    this._fetch_data();
}

    onChangeCustomFrom(ev) {
    this.state.filters.custom_range.from = ev.target.value;
    this._maybeFetchCustom();
    }

    onChangeCustomTo(ev) {
        this.state.filters.custom_range.to = ev.target.value;
        this._maybeFetchCustom();
    }

    _maybeFetchCustom() {
        if (this.state.filters.global_filter === "custom" &&
            this.state.filters.custom_range.from &&
            this.state.filters.custom_range.to) {
            this._fetch_data();
        }
    }

    onChangeTeamFilter(ev) {
        if (this.state.filters.global_filter === "custom") return;
        this.state.filters.team_filter = ev.target.value;
        this._fetch_data();
    }
    onChangePersonFilter(ev) {
        if (this.state.filters.global_filter === "custom") return;
        this.state.filters.person_filter = ev.target.value;
        this._fetch_data();
    }
    onChangeCustomerFilter(ev) {
        if (this.state.filters.global_filter === "custom") return;
        this.state.filters.customer_filter = ev.target.value;
        this._fetch_data();
    }
    onChangeOrderFilter(ev) {
        if (this.state.filters.global_filter === "custom") return;
        this.state.filters.order_filter = ev.target.value;
        this._fetch_data();
    }

    onChangeInvoiceFilter(ev) {
        if (this.state.filters.global_filter === "custom") return;
        this.state.filters.invoice_filter = ev.target.value;
        this._fetch_data();
    }
    onChangeProductFilter(ev) {
        if (this.state.filters.global_filter === "custom") return;
        this.state.filters.product_filter = ev.target.value;
        this._fetch_data();
    }
    onChangeProductCategory(ev) {
        const val = ev.target.value;
        this.state.filters.product_category_id = val ? parseInt(val) : null;
        this._fetch_data();
    }
    onChangeLowProductFilter(ev) {
        if (this.state.filters.global_filter === "custom") return;
        this.state.filters.low_product_filter = ev.target.value;
        this._fetch_data();
    }
    onChangeLowProductCategory(ev) {
        const val = ev.target.value;
        this.state.filters.low_product_category_id = val ? parseInt(val) : null;
        this._fetch_data();
    }
    onChangeOverdueFilter(ev) {
        if (this.state.filters.global_filter === "custom") return;
        this.state.filters.overdue_filter = ev.target.value;
        this._fetch_data();
    }
    onChangeNvRFilter(ev) {
        if (this.state.filters.global_filter === "custom") return;
        this.state.filters.nvrc_filter = ev.target.value;
        this._fetch_data();
    }
    onChangeGlobalLimit(ev) {
        this.state.filters.limit = parseInt(ev.target.value);
        this._fetch_data();
    }
}
SalesDashboard.template = "sales_management_dashboard.SalesDashboardTemplate";
registry.category("actions").add("sales_dashboard", SalesDashboard);
