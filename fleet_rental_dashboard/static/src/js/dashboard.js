/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { loadBundle } from "@web/core/assets";
import { Component, onMounted, onWillStart, proxy, signal } from "@odoo/owl";
const actionRegistry = registry.category("actions");

export class DashboardFleetRental extends Component {
    modal_warning = signal.ref();
    most_rented_cars_bar = signal.ref();
    most_rented_cars_line = signal.ref();
    most_rented_cars_pie = signal.ref();
    start_date = signal.ref();
    end_date = signal.ref();

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = proxy({
            top_customers: [],
            available_vehicle_details: [],
            available_cars: 0,
            running_cars: 0,
            running_vehicle_details: [],
        });

        // When the component is about to start, fetch data in tiles
        onWillStart(async () => {
            await loadBundle("web.chartjs_lib");
            await this.fetch_data();
        });
        // When the component is mounted, render various charts
        onMounted(async () => {
            await this.render_graphs();
        });
    }

    async render_graphs(startDate = false, endDate = false) {
        await this.render_most_rented_cars_bar(startDate, endDate);
    }

    async fetch_data(startDate = false, endDate = false) {
        const availability = await this.orm.call("car.rental.contract", "cars_availability", [startDate, endDate]);
        this.state.available_cars = availability['available_cars'];
        this.state.running_cars = availability['cars_running'];

        const details = await this.orm.call("car.rental.contract", "car_details", [startDate, endDate]);
        this.state.running_vehicle_details = details['running_details'] || [];
        this.state.available_vehicle_details = details['available_cars'] || [];

        this.state.top_customers = await this.orm.call("car.rental.contract", "top_customers", [startDate, endDate]) || [];
    }

    async render_most_rented_cars_bar(startDate = false, endDate = false) {
        if (!startDate) {
            startDate = this.start_date()?.value || document.getElementById("start_date")?.value || false;
        }
        if (!endDate) {
            endDate = this.end_date()?.value || document.getElementById("end_date")?.value || false;
        }

        const result = await this.orm.call('car.rental.contract', 'vehicle_most_rented', [startDate, endDate]);
            const colors = [
                '#6366f1', '#8b5cf6', '#a855f7', '#d946ef', '#ec4899', '#f43f5e',
                '#f97316', '#f59e0b', '#eab308', '#84cc16', '#22c55e', '#10b981',
                '#06b6d4', '#0ea5e9', '#3b82f6'
            ];
            const ctx = this.most_rented_cars_bar();
            const ctx2 = this.most_rented_cars_line();
            const ctx3 = this.most_rented_cars_pie();

            if (!ctx || !ctx2 || !ctx3) {
                return;
            }

            // Clean up existing chart instances safely
            if (this.chartStatus) {
                this.chartStatus.bar?.destroy();
                this.chartStatus.line?.destroy();
                this.chartStatus.pie?.destroy();
                this.chartStatus = null;
            }
            if (typeof Chart !== "undefined") {
                Chart.getChart(ctx)?.destroy();
                Chart.getChart(ctx2)?.destroy();
                Chart.getChart(ctx3)?.destroy();
            }

            const name = result.name || [];
            const count = result.num || [];

            // Create new chart instances
            const myChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: name,
                    datasets: [{
                        label: 'Count',
                        data: count,
                        backgroundColor: colors,
                        borderColor: colors,
                        barPercentage: 0.5,
                        barThickness: 60,
                        maxBarThickness: 80,
                        borderWidth: 1,
                    }]
                },
                options: {
                    scales: {
                        y: {
                            beginAtZero: true,
                        },
                    },
                    responsive: true,
                    maintainAspectRatio: false,
                }
            });

            const myChart2 = new Chart(ctx2, {
                type: 'line',
                data: {
                    labels: name,
                    datasets: [{
                        label: 'Count',
                        data: count,
                        backgroundColor: colors,
                        borderColor: colors[0] || '#6366f1',
                        borderWidth: 2,
                        tension: 0.3,
                        fill: false,
                    }]
                },
                options: {
                    scales: {
                        y: {
                            beginAtZero: true,
                        },
                    },
                    responsive: true,
                    maintainAspectRatio: false,
                }
            });

            const myChart3 = new Chart(ctx3, {
                type: 'pie',
                data: {
                    labels: name,
                    datasets: [{
                        label: 'Count',
                        data: count,
                        backgroundColor: colors,
                        borderColor: '#ffffff',
                        borderWidth: 2,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                }
            });

            // Save chart instances
            this.chartStatus = {
                bar: myChart,
                line: myChart2,
                pie: myChart3
            };
    }

    async onApplyFilter() {
        const startDate = this.start_date()?.value || document.getElementById("start_date")?.value || false;
        const endDate = this.end_date()?.value || document.getElementById("end_date")?.value || false;
        if (startDate && endDate) {
            if (startDate > endDate) {
                if (this.modal_warning()) {
                    this.modal_warning().style.display = "block";
                }
                return false;
            }
        }
        await this.fetch_data(startDate, endDate);
        await this.render_graphs(startDate, endDate);
    }

    async onClearFilter() {
        const startEl = this.start_date() || document.getElementById("start_date");
        const endEl = this.end_date() || document.getElementById("end_date");
        if (startEl) startEl.value = "";
        if (endEl) endEl.value = "";
        await this.fetch_data(false, false);
        await this.render_graphs(false, false);
    }

    closeModal() {
        if (this.modal_warning()) {
            this.modal_warning().style.display = "none";
        }
    }
}

DashboardFleetRental.template = "CustomDashBoard";
actionRegistry.add("fleet_rental_dashboard", DashboardFleetRental);
