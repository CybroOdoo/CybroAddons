/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, useRef, onPatched, onMounted, useState } from "@odoo/owl";
const actionRegistry = registry.category("actions");

export class DashboardFleetRental extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({
            top_customers: {},
            available_vehicle_details: {},
            available_cars: false,
            running_cars: {},
            running_vehicle_details: {},
        });
        this.modal_warning = useRef("modal_warning");
        this.most_rented_cars_bar = useRef("most_rented_cars_bar");
        this.most_rented_cars_line = useRef("most_rented_cars_line");
        this.most_rented_cars_pie = useRef("most_rented_cars_pie");
        this.start_date = useRef("start_date");
        this.end_date = useRef("end_date");
        // When the component is about to start, fetch data in tiles
        onWillStart(async () => {
            this.props.title = 'Dashboard';
            await this.fetch_data();
        });
        // When the component is mounted, render various charts
        onMounted(async () => {
            await this.render_graphs();
        });
    }
    render_graphs() {
        this.render_most_rented_cars_bar();
    }
    async fetch_data() {
        const availability = await this.orm.call("car.rental.contract", "cars_availability", []);
        this.state.available_cars = availability['available_cars'];
        this.state.running_cars = availability['cars_running'];

        const details = await this.orm.call("car.rental.contract", "car_details", []);
        this.state.running_vehicle_details = details['running_details'];
        this.state.available_vehicle_details = details['available_cars'];

        this.state.top_customers = await this.orm.call("car.rental.contract", "top_customers", []);
    }
    render_most_rented_cars_bar() {
        var self = this;
        // Destroy previous chart instances if they exist
        if (this.chartStatus) {
            if (this.chartStatus.bar) {
                this.chartStatus.bar.destroy();
            }
            if (this.chartStatus.line) {
                this.chartStatus.line.destroy();
            }
            if (this.chartStatus.pie) {
                this.chartStatus.pie.destroy();
            }
        }

        // Render new charts
        this.orm.call('car.rental.contract', 'vehicle_most_rented', [this.start_date.el.value, this.end_date.el.value]).then(result => {
            const colors = [
                '#6366f1', '#8b5cf6', '#a855f7', '#d946ef', '#ec4899', '#f43f5e',
                '#f97316', '#f59e0b', '#eab308', '#84cc16', '#22c55e', '#10b981',
                '#06b6d4', '#0ea5e9', '#3b82f6'
            ];
            var ctx = self.most_rented_cars_bar.el;
            var ctx2 = self.most_rented_cars_line.el;
            var ctx3 = self.most_rented_cars_pie.el;
            var name = result.name;
            var count = result.num;

            // Create new chart instances
            var myChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: name,
                    datasets: [{
                        label: 'Count',
                        data: count,
                        backgroundColor: colors,
                        borderColor: colors,
                        barPercentage: 0.5,
                        barThickness: 100,
                        maxBarThickness: 100,
                        minBarLength: 0,
                        borderWidth: 1,
                        fill: false
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
                }
            });

            var myChart2 = new Chart(ctx2, {
                type: 'line',
                data: {
                    labels: name,
                    datasets: [{
                        label: 'Count',
                        data: count,
                        backgroundColor: colors,
                        borderColor: colors,
                        barPercentage: 0.5,
                        barThickness: 6,
                        maxBarThickness: 8,
                        minBarLength: 0,
                        borderWidth: 1,
                        type: 'line',
                        fill: false
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
                }
            });

            var myChart3 = new Chart(ctx3, {
                type: 'pie',
                data: {
                    labels: name,
                    datasets: [{
                        label: 'Count',
                        data: count,
                        backgroundColor: colors,
                        borderColor: colors,
                        type: 'pie',
                        fill: false
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
                }
            });

            // Save chart instances
            this.chartStatus = {
                bar: myChart,
                line: myChart2,
                pie: myChart3
            };

        }).catch(error => {
            console.error('Error rendering chart:', error);
        });
    }
    onApplyFilter() {
        if (this.start_date.el.value && this.end_date.el.value) {
            if (this.start_date.el.value > this.end_date.el.value) {
                this.modal_warning.el.style.display = "block";
                return false
            }

        }
        this.render_graphs()
    }
    closeModal() {
        this.modal_warning.el.style.display = "none";
    }
}

DashboardFleetRental.template = "CustomDashBoard";
actionRegistry.add("fleet_rental_dashboard", DashboardFleetRental);
