/** @odoo-module **/

/**
 * CustomDashBoard
 * ----------------
 * This OWL component defines a custom dashboard for visualizing labor supply and worker details
 * in Odoo 17. It retrieves and displays various datasets through ORM calls, including:
 * - Workers availability
 * - Contract counts by customer and state
 * - Expected vs. Invoiced amounts
 * - Top customers
 * - Skill availability
 *
 * The dashboard utilizes Chart.js for rendering interactive graphs (bar, doughnut, and line charts).
 * Bootstrap is used for layout and responsiveness.
 */
import { registry } from "@web/core/registry";
import { onMounted, Component, useRef } from "@odoo/owl";
import { onWillStart, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

const actionRegistry = registry.category("actions");

export class CustomDashBoard extends Component {
    static template = 'CustomDashBoard';
    static props = ["*"];
    setup() {
        this.rootRef = useRef('abcd');
        this.canvasRef = useRef("top_product_button");
        this.orm = useService("orm");
        this.state = useState({
            labour_supply_details: [],
            customers: [],
            total_invoiced_amount: [],
            skills: [],
            expected_amount: [],
            workers: [],
        });
        onWillStart(async () => {
            this.props.title = 'Dashboard';
            await this.fetch_data();
        });
        onMounted(async () => {
            await this.render_graphs();
        });
    }
    /**
     * Fetch all required datasets from the backend via RPC.
     */
    async fetch_data() {
        const results = await Promise.all([
            this.orm.call('workers.details', 'get_labour_supply_details'),
            this.orm.call('workers.details', 'get_top_customer'),
            this.orm.call('workers.details', 'get_total_invoiced_amount'),
            this.orm.call('workers.details', 'get_skills_available'),
            this.orm.call('workers.details', 'get_expected_amount'),
            this.orm.call('workers.details', 'get_workers_available')
        ]);
        this.state.labour_supply_details = results[0]?.ongoing_contract || [];
        this.state.customers = results[1]?.customer || [];
        this.state.total_invoiced_amount = results[2]?.invoiced_amount || 0;
        this.state.skills = results[3]?.skill || [];
        this.state.expected_amount = results[4]?.expected_amount || 0;
        this.state.workers = results[5]?.workers || [];
    }
    /**
     * Render all graphs after component is mounted.
     */
    async render_graphs() {
        await this.render_get_workers_count();
        await this.render_get_contract_count_state();
        await this.render_get_contract_count_customer();
        await this.render_get_contract_amount();
    }
    /**
     * Triggered when dropdown filter changes.
     * Fetches and renders a bar chart for contract amount by filter option (e.g. state, customer, etc.).
     * @param {Event} events
     */
    onchange_selection(events) {
        var option = $(events.target).val();
        var self = this;
        this.orm.call("workers.details", "get_details_amount", [option])
            .then(function (array) {
                var ctx = self.rootRef.el.querySelector("#labour_contract");
                var myChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: array.sequence,
                        datasets: [{
                            label: 'Hide',
                            data: array.amount,
                            backgroundColor: [/* colors */],
                            borderColor: [/* border colors */],
                            barPercentage: 0.5,
                            barThickness: 6,
                            borderWidth: 1
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true
                            },
                        },
                        responsive: true,
                        maintainAspectRatio: false,
                        legend: {
                            display: true,
                            position: "right"
                        }
                    }
                });
            });
    }
    /**
     * Render doughnut chart for worker availability by state.
     */
    render_get_workers_count() {
        var self = this;
        this.orm.call("workers.details", "get_workers_count", [])
            .then((result) => {
                var ctx = self.rootRef.el.querySelector("#worker_availability");
                var myChart = new Chart(ctx, {
                    type: 'doughnut',
                    data: {
                        labels: result.state,
                        datasets: [{
                            label: 'Workers',
                            data: result.count,
                            backgroundColor: [/* colors */],
                            borderColor: ["#003f5c"],
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false
                    }
                });
            });
    }
    /**
     * Render line chart of contract counts grouped by state.
     */
    render_get_contract_count_state() {
        var self = this;
        this.orm.call("workers.details", "get_contract_count_state", [])
            .then(function (arrays) {
                var ctx = self.rootRef.el.querySelector(".contract");
                var myChart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: arrays.state,
                        datasets: [{
                            label: 'Hide',
                            data: arrays.count,
                            backgroundColor: '#003f5c',
                            borderColor: '#003f5c',
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        legend: {
                            display: true,
                            position: "right"
                        },
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        }
                    }
                });
            });
    }
    /**
     * Render bar chart showing contract counts by customer.
     */
    render_get_contract_count_customer() {
        var self = this;
        this.orm.call("workers.details", "get_contract_count_customer", [])
            .then(function (arrays) {
                var ctx = self.rootRef.el.querySelector(".customer_contract");
                var myChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: arrays.name,
                        datasets: [{
                            label: 'Hide',
                            data: arrays.count,
                            backgroundColor: [/* colors */],
                            borderColor: [/* border colors */],
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        legend: {
                            display: true,
                            position: "right"
                        },
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        }
                    }
                });
            });
    }
    /**
     * Render bar chart showing contract amounts grouped by sequence.
     */
    render_get_contract_amount() {
        var self = this;
        this.orm.call("workers.details", "get_contract_amount", [])
            .then(function (arrays) {
                var ctx = self.rootRef.el.querySelector(".labour_contract");
                var myChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: arrays.sequence,
                        datasets: [{
                            label: 'Hide',
                            data: arrays.amount,
                            backgroundColor: [/* colors */],
                            borderColor: [/* border colors */],
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        legend: {
                            display: true,
                            position: "right"
                        },
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        }
                    }
                });
            });
    }
}
// Register the dashboard action
actionRegistry.add("labour_supply_dashboard", CustomDashBoard);
