/** @odoo-module **/
import { Component, useState, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { useService } from "@web/core/utils/hooks";
/**
 * DashboardAction component handles the display and interaction
 * of the fleet management dashboard. It manages data fetching,
 * filtering, and displaying charts and lists.
 */
export class DashboardAction extends Component {
    /**
     * Initializes component state and fetches initial data.
     */
    static props = {
        action: Object,
        actionId: Number,
        updateActionState: Function,
        className: { type: String, optional: true },
    };

    async setup() {
        this.state = useState({
            flag: null,
            admin_odometer_list: [],
            admin_fleet_cost_list: [],
            admin_recurring_list: [],
            fleet_vehicle_list: [],
            fleet_model_list: [],
            fleet_manufacture_list: [],
            odometer_value: null,
            service_value: null,
            recurring_value: null,
            all_vehicles: null,
            fleet_state: [],
            manufacture_list: [],
            model_list: [],
            data: { drivers: [], vehicles: [], manufactures: [] },
        });

        this.filter = useRef("filters");
        this.fleet_main = useRef("fleet_main");
        this.action = useService("action");
        await this.ensureGoogleChartsLoaded();
        await this.fetch_data();
        this.state.data = await this.render_filter();
    }
    /**
     * Handles filter change events and updates the dashboard data.
     */
    async ensureGoogleChartsLoaded() {
        if (typeof window === "undefined") {
            return;
        }
        if (window.google && window.google.charts && window.google.visualization) {
            return;
        }
        if (!document.querySelector('script[data-gcharts-loader]')) {
            const s = document.createElement("script");
            s.setAttribute("data-gcharts-loader", "1");
            s.src = "https://www.gstatic.com/charts/loader.js";
            document.head.appendChild(s);
            await new Promise((resolve, reject) => {
                s.onload = resolve;
                s.onerror = () => reject(new Error("Failed to load google charts loader.js"));
            });
        } else {
        }
        await new Promise((resolve) => {
            window.google.charts.load("current", { packages: ["corechart"] });
            window.google.charts.setOnLoadCallback(() => resolve());
        });
    }
    /**
     * Opens the Manufacturers view based on the current state.
     */

    async _onchangeFilter() {
        try {
            const data = {
                date: this.filter.el.querySelector("#date_filter").value,
                vehicle: this.filter.el.querySelector("#vehicle_selection").value,
                driver: this.filter.el.querySelector("#driver_selection").value,
                manufacturer: this.filter.el.querySelector("#manufacturers_selection").value,
            };

            const result = await rpc("/fleet_advanced_dashboard/filter_data", { data });
            if (!result) {
                return;
            }

            this.state.admin_odometer_list = result.admin_odometer_list || [];
            this.state.admin_fleet_cost_list = result.admin_fleet_cost_list || [];
            this.state.admin_recurring_list = result.admin_recurring_list || [];
            this.state.fleet_vehicle_list = result.fleet_vehicle_list || [];
            this.state.fleet_model_list = result.fleet_model_list || [];
            this.state.fleet_manufacture_list = result.fleet_manufacture_list || [];

            this.state.all_vehicles = result.total_vehicles || this.state.all_vehicles;
            this.state.odometer_value = result.total_odometer ?? this.state.odometer_value;
            this.state.service_value = result.service_cost ?? this.state.service_value;
            this.state.recurring_value = result.recurring_cost ?? this.state.recurring_value;

            this.redrawCharts(result);

        } catch (err) {
        }
    }
    async fetch_data() {
        try {
            const result = await rpc("/web/dataset/call_kw", {
                model: "fleet.vehicle",
                method: "get_tiles_data",
                args: [],
                kwargs: {},
            });

            if (!result) {
                return;
            }

            this.state.odometer_value = result.total_odometer;
            this.state.service_value = result.service_cost;
            this.state.recurring_value = result.recurring_cost;
            this.state.all_vehicles = result.all_vehicles;
            this.state.fleet_state = result.fleet_state || [];
            this.state.flag = result.flag;

            if (this.state.flag === 0) {
                this.state.manufacture_list = result.manufacture_list || [];
                this.state.model_list = result.model_list || [];
            } else {
                this.state.admin_odometer_list = result.admin_odometer_list || [];
                this.state.admin_fleet_cost_list = result.admin_fleet_cost_list || [];
                this.state.admin_recurring_list = result.admin_recurring_list || [];
                this.state.fleet_vehicle_list = result.fleet_vehicle_list || [];
                this.state.fleet_model_list = result.fleet_model_list || [];
                this.state.fleet_manufacture_list = result.fleet_manufacture_list || [];
            }

            this.redrawCharts(result);
        } catch (err) {
        }
    }

    clearContainer(selector) {
        const el = this.fleet_main.el.querySelector(selector);
        if (el) {
            el.innerHTML = "";
        }
        return el;
    }


    redrawCharts(filtered_result) {
        try {
            if (!window.google || !window.google.visualization) {
                return;
            }

            const lineContainer = this.clearContainer("#lineChart");
            if (lineContainer && Array.isArray(filtered_result.odometer_value_list)) {
                try {
                    const lineData = google.visualization.arrayToDataTable(filtered_result.odometer_value_list);
                    const lineChart = new google.visualization.LineChart(lineContainer);
                    lineChart.draw(lineData, {
                        title: "Odometer Reading Monthly Wise",
                        hAxis: { title: "Month" },
                        vAxis: { title: "Odometer Values" },
                        legend: "none",
                        pointsVisible: true,
                    });
                } catch (err) {
                    lineContainer.innerHTML = '<div style="padding:40px;text-align:center;color:#777">Odometer chart unavailable</div>';
                }
            }

            const serviceContainer = this.clearContainer("#service_Chart");
            const hasServiceData =
                Array.isArray(filtered_result.service_type) && filtered_result.service_type.length > 1 &&
                filtered_result.service_type.slice(1).some(row => Array.isArray(row) && row[1] && Number(row[1]) > 0);

            if (!serviceContainer) {
            } else if (!hasServiceData) {
                serviceContainer.innerHTML = `
                    <div style="text-align:center; padding:140px 20px; color:#777; font-size:18px;">
                        No Service Data Available
                    </div>
                `;
            } else {
                try {
                    const pieData = google.visualization.arrayToDataTable(filtered_result.service_type);
                    const pieChart = new google.visualization.PieChart(serviceContainer);
                    pieChart.draw(pieData, {
                        title: "Service Types",
                        pieHole: 0.4,
                    });
                } catch (err) {
                    serviceContainer.innerHTML = '<div style="padding:40px;text-align:center;color:#777">Service chart unavailable</div>';
                }
            }

            const barContainer = this.clearContainer("#barChart");
            if (barContainer && Array.isArray(filtered_result.service_cost_list)) {
                const hasBarData = filtered_result.service_cost_list.slice(1).some(row => Array.isArray(row) && Number(row[1]) && Number(row[1]) !== 0);
                if (!hasBarData) {
                    barContainer.innerHTML = `
                        <div style="text-align:center; padding:140px 20px; color:#777; font-size:18px;">
                            No Service Cost Data Available
                        </div>
                    `;
                } else {
                    try {
                        const barData = google.visualization.arrayToDataTable(filtered_result.service_cost_list);
                        const barChart = new google.visualization.ColumnChart(barContainer);
                        barChart.draw(barData, {
                            title: "Service Cost Last Six Months",
                            vAxis: { gridlines: { color: "transparent" }, title: "Service Cost" },
                            legend: "none",
                        });
                    } catch (err) {
                        barContainer.innerHTML = '<div style="padding:40px;text-align:center;color:#777">Service cost chart unavailable</div>';
                    }
                }
            }
        } catch (err) {
        }
    }

    _onClickOdoMeter() {
        if (this.state.flag === true) {
            this.action.doAction({
                type: "ir.actions.act_window",
                name: "Odometers",
                res_model: "fleet.vehicle.odometer",
                domain: [["id", "in", this.state.admin_odometer_list]],
                view_mode: "list",
                views: [[false, "list"], [false, "form"]],
                target: "self",
            });
        }
    }

    OpenVehicleModelBrand(domain) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Manufacturers",
            res_model: "fleet.vehicle.model.brand",
            domain: [["id", "in", domain]],
            view_mode: "kanban",
            views: [[false, "kanban"], [false, "form"]],
            target: "self",
        });
    }

    OpenVehicleModel(domain) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Models",
            res_model: "fleet.vehicle.model",
            domain: [["id", "in", domain]],
            view_mode: "kanban",
            views: [[false, "kanban"], [false, "form"]],
            target: "self",
        });
    }

    _onClickManufacturers() {
        this.OpenVehicleModelBrand(this.state.fleet_manufacture_list);
    }

    _onClickModels() {
        this.OpenVehicleModel(this.state.fleet_model_list);
    }

    _onClickVehicles() {
        if (this.state.flag == 1) {
            this.action.doAction({
                type: "ir.actions.act_window",
                name: "Vehicles",
                res_model: "fleet.vehicle",
                view_mode: "kanban",
                views: [[false, "kanban"], [false, "form"]],
                domain: [["id", "in", this.state.fleet_vehicle_list]],
                target: "self",
            });
        }
    }

    _onClickServices() {
        if (this.state.flag == 1) {
            this.action.doAction({
                type: "ir.actions.act_window",
                name: "Services",
                res_model: "fleet.vehicle.log.services",
                domain: [["id", "in", this.state.admin_fleet_cost_list]],
                view_mode: "list",
                views: [[false, "list"], [false, "form"]],
                target: "self",
            });
        }
    }

    _onClickContracts() {
        if (this.state.flag == 1) {
            this.action.doAction({
                type: "ir.actions.act_window",
                name: "Vehicles",
                res_model: "fleet.vehicle.log.contract",
                domain: [["id", "in", this.state.admin_recurring_list]],
                view_mode: "kanban",
                views: [[false, "list"], [false, "form"]],
                target: "self",
            });
        }
    }

    async render_filter() {
        try {
            const { drivers, vehicles, manufactures } = await rpc("/fleet/filter", {});
            return { drivers, vehicles, manufactures };
        } catch (err) {
            return { drivers: [], vehicles: [], manufactures: [] };
        }
    }
}

DashboardAction.template = "fleet_advanced_dashboard.FleetDashBoard";

registry.category("actions").add("fleet_advanced_dashboard.action", DashboardAction);
