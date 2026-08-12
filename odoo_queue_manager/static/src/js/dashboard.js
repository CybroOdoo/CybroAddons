/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Component, onWillStart, onMounted, useState, useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { loadJS } from "@web/core/assets";

const actionRegistry = registry.category("actions");

class QueueDashboard extends Component {
    /** Dashboard component for displaying queue analytics, charts, and filters */
    setup() {
        this.orm = useService('orm');
        this.rootRef = useRef('root');
        this.fromDate = useRef('fromDate');
        this.toDate = useRef('toDate');
        this.state = useState({
            total_token: [],
            colors: [],
            MoveData: [],
            token_data: [],
            fromDateValue: null,
            toDateValue: null,
        });

        onWillStart(async () => {
            await loadJS("/web/static/lib/Chart/Chart.js");
            this.props.title = 'Dashboard';
            // Set default date range (last 10 days)
            const today = new Date();
            const tenDaysAgo = new Date(today);
            tenDaysAgo.setDate(today.getDate() - 10);

            this.state.fromDateValue = this.formatDate(tenDaysAgo);
            this.state.toDateValue = this.formatDate(today);
        });

        onMounted(async () => {
            // Set the date inputs to default values
            if (this.fromDate.el) {
                this.fromDate.el.value = this.state.fromDateValue;
            }
            if (this.toDate.el) {
                this.toDate.el.value = this.state.toDateValue;
            }
            await this.render_graphs();
        });
    }

    formatDate(date) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }

    async render_graphs() {
        await this.render_operation_tile();
        await this.render_pie_chart();
        await this.render_table();
    }
    async render_table() {
        const result = await this.orm.call("token.token", "get_table_data",
            [], {
                from_date: this.state.fromDateValue,
                to_date: this.state.toDateValue
            }
        );
        this.state.token_data = result;
    }
    async render_operation_tile() {
        const result = await this.orm.call('token.token', 'get_tokens',
            [], {
                from_date: this.state.fromDateValue,
                to_date: this.state.toDateValue
            }
        );
        this.state.total_token = result;
        this.state.colors = ["red", "blue", "green", "orange", "purple", "steel", "rebecca", "brown", "pink", "grey", "black"];
    }

    async render_pie_chart() {
        try {
            const result = await this.orm.call(
                'token.token',
                'pie_function',
                [],
                {
                    from_date: this.state.fromDateValue,
                    to_date: this.state.toDateValue
                }
            );
            const name = result.name;
            const count = result.count;

            // Destroy old chart if exists
            if (this.chart) {
                this.chart.destroy();
            }

            const ctx = this.rootRef.el.querySelector("#stock_moves");

            // Safety check (VERY important in OWL)
            if (!ctx) {
                console.warn("Chart canvas not found");
                return;
            }

            this.chart = new Chart(ctx, {
                type: 'pie',
                data: {
                    labels: name,
                    datasets: [{
                        data: count,
                        backgroundColor: [
                            "#0d6efd",
                            "#198754",
                            "#fd7e14",
                            "#dc3545",
                            "#6f42c1"
                        ],
                        borderWidth: 1,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });

        } catch (error) {
            console.error("Chart rendering error:", error);
            if (this.env.services.notification) {
                this.env.services.notification.add(
                    "Failed to load chart data",
                    { type: "danger" }
                );
            }
        }
    }

    // On clicking tiles
    async onclick_tiles(f) {
        var domain;
        const id = Number(f.currentTarget.dataset.id);

        // Use the current filter dates
        const fromDateValue = this.state.fromDateValue;
        const toDateValue = this.state.toDateValue;

        // Convert to datetime strings for domain
        const startDateTime = fromDateValue + ' 00:00:00';
        const endDateTime = toDateValue + ' 23:59:59';

        if (id === 1) {
            domain = [
                ['state', 'in', ['draft', 'in_progress', 'done', 'cancelled']],
                ['token_datetime', '>=', startDateTime],
                ['token_datetime', '<=', endDateTime]
            ];
        }
        if (id === 2) {
            domain = [
                ['state', '=', 'done'],
                ['token_datetime', '>=', startDateTime],
                ['token_datetime', '<=', endDateTime]
            ];
        }
        if (id === 3) {
            domain = [
                ['state', '=', 'draft'],
                ['token_datetime', '>=', startDateTime],
                ['token_datetime', '<=', endDateTime]
            ];
        }

        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };

        this.env.services['action'].doAction({
            name: 'Token',
            type: 'ir.actions.act_window',
            res_model: 'token.token',
            views: [[false, 'list'], [false, 'form']],
            view_mode: 'list,form',
            domain: domain,
            target: 'current',
        }, options);
    }

    async onchange_stock_moves_selection(events) {
        const option = events.target.value;
        const today = new Date();
        let fromDate, toDate;

        if (option === 'today') {
            fromDate = today;
            toDate = today;
        } else if (option === 'custom') {
            // Don't update dates, let user select them manually
            return;
        } else {
            // Handle numeric options (10, 20, 30 days)
            const days = parseInt(option);
            toDate = today;
            fromDate = new Date(today);
            fromDate.setDate(today.getDate() - days);
        }

        this.state.fromDateValue = this.formatDate(fromDate);
        this.state.toDateValue = this.formatDate(toDate);

        // Update the date inputs
        if (this.fromDate.el) {
            this.fromDate.el.value = this.state.fromDateValue;
        }
        if (this.toDate.el) {
            this.toDate.el.value = this.state.toDateValue;
        }

        // Re-render all graphs with new date range
        await this.render_graphs();
    }

    async onchange_custom_date() {
        // Get values from date inputs
        const fromDateValue = this.fromDate.el.value;
        const toDateValue = this.toDate.el.value;

        // Only update if both dates are selected
        if (fromDateValue && toDateValue) {
            this.state.fromDateValue = fromDateValue;
            this.state.toDateValue = toDateValue;

            // Re-render all graphs with new date range
            await this.render_graphs();
        }
    }
}

QueueDashboard.template = "odoo_queue_manager.QueueDashboard";
actionRegistry.add("odoo_queue_manager_dashboard_tag", QueueDashboard);
