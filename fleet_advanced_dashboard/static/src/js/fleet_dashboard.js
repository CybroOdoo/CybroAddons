/** @odoo-module **/
import { Component, proxy, signal, onWillStart, onMounted, onWillUnmount, useProps } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { useService } from "@web/core/utils/hooks";
import { standardActionServiceProps } from "@web/webclient/actions/action_plugin";
/**
 * DashboardAction component handles the display and interaction
 * of the fleet management dashboard. It manages data fetching,
 * filtering, and displaying charts and lists.
 */
export class DashboardAction extends Component {
    static template = "fleet_advanced_dashboard.FleetDashBoard";
    props = useProps(standardActionServiceProps);

    filtersRef = signal.ref();
    fleetMainRef = signal.ref();

    get filters() {
        return this.filtersRef;
    }

    get filter() {
        return { el: this.filtersRef() };
    }

    get fleet_main() {
        return { el: this.fleetMainRef() };
    }

    setup() {
        this.state = proxy({
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

        this.action = useService("action");
        this.orm = useService("orm");

        this.onResize = () => {
            if (this.lastChartResult && this.fleetMainRef()) {
                this.redrawCharts(this.lastChartResult);
            }
        };
        window.addEventListener("resize", this.onResize);
        onWillUnmount(() => {
            window.removeEventListener("resize", this.onResize);
        });

        onWillStart(async () => {
            const chartPromise = this.ensureGoogleChartsLoaded();
            const dataPromise = this.fetch_data();
            const filterPromise = this.render_filter().then((d) => {
                this.state.data = d;
            });
            await Promise.allSettled([chartPromise, dataPromise, filterPromise]);
        });

        onMounted(async () => {
            await this.ensureGoogleChartsLoaded();
            if (this.lastChartResult) {
                this.redrawCharts(this.lastChartResult);
            }
        });
    }
    /**
     * Ensures Google Charts library is loaded dynamically.
     */
    async ensureGoogleChartsLoaded() {
        if (typeof window === "undefined") {
            return;
        }
        if (window.google?.charts?.load && window.google?.visualization) {
            return;
        }
        if (!window._googleChartsLoadingPromise) {
            window._googleChartsLoadingPromise = (async () => {
                if (!window.google?.charts) {
                    await new Promise((resolve) => {
                        const existing = document.querySelector('script[src*="charts/loader.js"]');
                        if (existing) {
                            if (window.google?.charts) return resolve();
                            existing.addEventListener("load", resolve, { once: true });
                            existing.addEventListener("error", resolve, { once: true });
                            setTimeout(resolve, 3000);
                            return;
                        }
                        const s = document.createElement("script");
                        s.src = "https://www.gstatic.com/charts/loader.js";
                        s.onload = resolve;
                        s.onerror = resolve;
                        document.head.appendChild(s);
                        setTimeout(resolve, 3000);
                    });
                }
                if (window.google?.charts) {
                    await new Promise((resolve) => {
                        try {
                            window.google.charts.load("current", { packages: ["corechart"] });
                            window.google.charts.setOnLoadCallback(() => resolve());
                            setTimeout(resolve, 3000);
                        } catch (err) {
                            resolve();
                        }
                    });
                }
            })();
        }
        await window._googleChartsLoadingPromise;
    }

    /**
     * Handles filter change events and updates the dashboard data.
     */
    async _onchangeFilter() {
        try {
            const filterEl = this.filtersRef() || this.filter.el;
            if (!filterEl) {
                return;
            }
            const data = {
                date: filterEl.querySelector("#date_filter")?.value,
                vehicle: filterEl.querySelector("#vehicle_selection")?.value,
                driver: filterEl.querySelector("#driver_selection")?.value,
                manufacturer: filterEl.querySelector("#manufacturers_selection")?.value,
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

            this.lastChartResult = result;
            this.redrawCharts(result);
        } catch {
            return;
        }
    }

    async fetch_data() {
        try {
            const result = await this.orm.call("fleet.vehicle", "get_tiles_data");

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
                this.state.fleet_manufacture_list = result.fleet_manufacture_list || result.manufacture_list || [];
                this.state.fleet_model_list = result.fleet_model_list || result.model_list || [];
            } else {
                this.state.admin_odometer_list = result.admin_odometer_list || [];
                this.state.admin_fleet_cost_list = result.admin_fleet_cost_list || [];
                this.state.admin_recurring_list = result.admin_recurring_list || [];
                this.state.fleet_vehicle_list = result.fleet_vehicle_list || [];
                this.state.fleet_model_list = result.fleet_model_list || [];
                this.state.fleet_manufacture_list = result.fleet_manufacture_list || [];
            }

            this.lastChartResult = result;
            this.redrawCharts(result);
        } catch {
            return;
        }
    }

    clearContainer(selector) {
        const rootEl = this.fleetMainRef() || this.fleet_main?.el;
        const el = rootEl ? rootEl.querySelector(selector) : document.querySelector(selector);
        if (el) {
            el.innerHTML = "";
        }
        return el;
    }


    redrawCharts(filtered_result) {
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
            } catch {
                lineContainer.innerHTML = '<div style="padding:40px;text-align:center;color:#777">Odometer chart unavailable</div>';
            }
        }

        const serviceContainer = this.clearContainer("#service_Chart");
        if (serviceContainer) {
            const hasServiceData =
                Array.isArray(filtered_result.service_type) && filtered_result.service_type.length > 1 &&
                filtered_result.service_type.slice(1).some(row => Array.isArray(row) && row[1] && Number(row[1]) > 0);

            if (!hasServiceData) {
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
                } catch {
                    serviceContainer.innerHTML = '<div style="padding:40px;text-align:center;color:#777">Service chart unavailable</div>';
                }
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
                } catch {
                    barContainer.innerHTML = '<div style="padding:40px;text-align:center;color:#777">Service cost chart unavailable</div>';
                }
            }
        }
    }

    _onClickOdoMeter() {
        if (this.state.flag == 1) {
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
                name: "Contracts",
                res_model: "fleet.vehicle.log.contract",
                domain: [["id", "in", this.state.admin_recurring_list]],
                view_mode: "list",
                views: [[false, "list"], [false, "form"]],
                target: "self",
            });
        }
    }

    async render_filter() {
        try {
            const { drivers, vehicles, manufactures } = await rpc("/fleet_advanced_dashboard/filter", {});
            return { drivers, vehicles, manufactures };
        } catch {
            return { drivers: [], vehicles: [], manufactures: [] };
        }
    }
}

registry.category("actions").add("fleet_advanced_dashboard.action", DashboardAction);
