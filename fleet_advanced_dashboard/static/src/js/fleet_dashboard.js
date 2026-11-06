/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Component, onWillStart, onMounted, useState, useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";
import { loadJS } from "@web/core/assets";

export class FleetDashboard extends Component {
    setup() {
        super.setup(...arguments);
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
            // Holds the currently selected filter values (string IDs or 'null')
            selectedVehicle: 'null',
            selectedDriver: 'null',
            selectedManufacturer: 'null',
            selectedDate: 'null',
            data: {
                "drivers": [],
                "vehicles": [],
                "manufactures": []
            }
        });
        this.filter = useRef("filters");
        this.fleet_main = useRef("fleet_main");
        this.action = useService("action");
        this.orm = useService("orm");
        this.lastChartData = null;

        onWillStart(async () => {
            await loadJS("https://www.gstatic.com/charts/loader.js");
            await new Promise((resolve) => {
                if (window.google && window.google.charts) {
                    google.charts.load('current', {
                        packages: ['corechart']
                    });
                    google.charts.setOnLoadCallback(resolve);
                } else {
                    resolve();
                }
            });
            this.state.data = await this.render_filter();
            await this.fetch_data();
        });

        onMounted(() => {
            if (this.lastChartData) {
                this.renderCharts(
                    this.lastChartData.odometer,
                    this.lastChartData.serviceType,
                    this.lastChartData.serviceCost
                );
            }
        });
    }

    /**
     * Renders google charts into the dashboard elements.
     */
    renderCharts(odometerList, serviceTypeList, serviceCostList) {
        if (!this.fleet_main.el || !window.google || !google.visualization) {
            return;
        }
        try {
            const lineChartEl = this.fleet_main.el.querySelector('#lineChart');
            if (lineChartEl && odometerList && odometerList.length) {
                const data = google.visualization.arrayToDataTable(odometerList);
                const options = {
                    title: 'Monthly Odometer Reading',
                    hAxis: { title: 'Month' },
                    vAxis: { title: 'Odometer Values' },
                    legend: 'none',
                    pointsVisible: true,
                };
                const lineChart = new google.visualization.LineChart(lineChartEl);
                lineChart.draw(data, options);
            }

            const serviceChartEl = this.fleet_main.el.querySelector('#service_Chart');
            if (serviceChartEl && serviceTypeList && serviceTypeList.length) {
                const serviceData = google.visualization.arrayToDataTable(serviceTypeList);
                const serviceOptions = {
                    title: 'Service Types',
                    pieHole: 0.4
                };
                const serviceChart = new google.visualization.PieChart(serviceChartEl);
                serviceChart.draw(serviceData, serviceOptions);
            }

            const barChartEl = this.fleet_main.el.querySelector('#barChart');
            if (barChartEl && serviceCostList && serviceCostList.length) {
                const bData = google.visualization.arrayToDataTable(serviceCostList);
                const bOptions = {
                    title: 'Service Cost Last Six Months',
                    vAxis: {
                        gridlines: { color: 'transparent' },
                        title: 'Service Cost'
                    },
                    legend: 'none',
                };
                const barChart = new google.visualization.ColumnChart(barChartEl);
                barChart.draw(bData, bOptions);
            }
        } catch (e) {
            console.error('Fleet dashboard chart error:', e);
        }
    }

    /**
     * Handles filter change events and updates the dashboard data.
     */
    async _onchangeFilter() {
        if (!this.filter.el) return;
        // Read current filter values from the DOM
        const date = this.filter.el.querySelector('#date_filter').value;
        const vehicle = this.filter.el.querySelector('#vehicle_selection').value;
        const driver = this.filter.el.querySelector('#driver_selection').value;
        const manufacturer = this.filter.el.querySelector('#manufacturers_selection').value;

        // Persist selected values so other methods (e.g. fetch_data) can use them
        this.state.selectedVehicle = vehicle;
        this.state.selectedDriver = driver;
        this.state.selectedManufacturer = manufacturer;
        this.state.selectedDate = date;

        // Await the filter RPC so state is updated before charts redraw
        try {
            const result = await rpc('/fleet_advanced_dashboard/filter_data', {
                'data': {
                    'date': date,
                    'vehicle': vehicle,
                    'driver': driver,
                    'manufacturer': manufacturer,
                }
            });
            this.state.odometer_value = result[0];
            this.state.service_value = result[1];
            this.state.recurring_value = result[2];
            this.state.admin_odometer_list = result[3];
            this.state.admin_fleet_cost_list = result[4];
            this.state.admin_recurring_list = result[5];
            this.state.fleet_vehicle_list = result[6];
            this.state.fleet_model_list = result[7];
            this.state.fleet_manufacture_list = result[8];
            this.state.all_vehicles = result[9];

            const serviceCostList = result[10];
            const odometerValueList = result[11];
            const serviceTypeList = result[12];

            this.lastChartData = {
                odometer: odometerValueList,
                serviceType: serviceTypeList,
                serviceCost: serviceCostList
            };
            this.renderCharts(odometerValueList, serviceTypeList, serviceCostList);
        } catch (e) {
            console.error('Fleet dashboard filter error:', e);
        }
    }

    /**
     * Opens the Manufacturers view based on the current state.
     */
    _onClickManufacturers() {
        const list = (this.state.fleet_manufacture_list && this.state.fleet_manufacture_list.length)
            ? this.state.fleet_manufacture_list
            : this.state.manufacture_list;
        this.OpenVehicleModelBrand(list);
    }

    /**
     * Opens the vehicle model brand view with a specific domain.
     * @param {Array} domain - The domain to filter the records.
     */
    OpenVehicleModelBrand(domain) {
        const domainFilter = (domain && domain.length) ? [["id", "in", domain]] : [];
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'Manufacturers',
            res_model: 'fleet.vehicle.model.brand',
            domain: domainFilter,
            view_mode: 'kanban,list,form',
            views: [[false, 'kanban'], [false, 'list'], [false, 'form']],
            target: 'current'
        });
    }

    /**
     * Opens the Models view based on the current state.
     */
    _onClickModels() {
        const list = (this.state.fleet_model_list && this.state.fleet_model_list.length)
            ? this.state.fleet_model_list
            : this.state.model_list;
        this.OpenVehicleModel(list);
    }

    /**
     * Opens the vehicle model view with a specific domain.
     * @param {Array} domain - The domain to filter the records.
     */
    OpenVehicleModel(domain) {
        const domainFilter = (domain && domain.length) ? [["id", "in", domain]] : [];
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'Models',
            res_model: 'fleet.vehicle.model',
            domain: domainFilter,
            view_mode: 'list,kanban,form',
            views: [[false, 'list'], [false, 'kanban'], [false, 'form']],
            target: 'current'
        });
    }

    /**
     * Opens the Vehicles view based on the current state.
     */
    _onClickVehicles() {
        const list = this.state.fleet_vehicle_list;
        const domain = (list && list.length) ? [["id", "in", list]] : [];
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'Vehicles',
            res_model: 'fleet.vehicle',
            view_mode: 'kanban,list,form',
            views: [[false, 'kanban'], [false, 'list'], [false, 'form']],
            domain: domain,
            target: 'current'
        });
    }

    /**
     * Opens the Contracts view based on the current state.
     */
    _onClickContracts() {
        const list = this.state.admin_recurring_list;
        const domain = (list && list.length) ? [["id", "in", list]] : [];
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'Contracts',
            res_model: 'fleet.vehicle.log.contract',
            domain: domain,
            view_mode: 'list,kanban,form',
            views: [[false, 'list'], [false, 'kanban'], [false, 'form']],
            target: 'current'
        });
    }

    /**
     * Opens the Services view based on the current state.
     */
    _onClickServices() {
        const list = this.state.admin_fleet_cost_list;
        const domain = (list && list.length) ? [["id", "in", list]] : [];
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'Services',
            res_model: 'fleet.vehicle.log.services',
            domain: domain,
            view_mode: 'list,form',
            views: [[false, 'list'], [false, 'form']],
            target: 'current'
        });
    }

    /**
     * Opens the Odometers view based on the current state.
     */
    _onClickOdoMeter() {
        const list = this.state.admin_odometer_list;
        const domain = (list && list.length) ? [["id", "in", list]] : [];
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'Odometers',
            res_model: 'fleet.vehicle.odometer',
            domain: domain,
            view_mode: 'list,form',
            views: [[false, 'list'], [false, 'form']],
            target: 'current'
        });
    }

    /**
     * Fetches filter data for the dashboard.
     * @returns {Object} The filter data including drivers, vehicles, and manufactures.
     */
    async render_filter() {
        const { drivers, vehicles, manufactures } = await rpc('/fleet/filter', {});
        return { drivers, vehicles, manufactures };
    }

    /**
     * Fetches data for the dashboard and prepares charts data using ORM service.
     */
    async fetch_data() {
        try {
            const result = await this.orm.call('fleet.vehicle', 'get_tiles_data', [this.state.selectedVehicle]);
            this.state.odometer_value = result['total_odometer'];
            this.state.service_value = result['service_cost'];
            this.state.recurring_value = result['recurring_cost'];
            this.state.all_vehicles = result['all_vehicles'];
            this.state.fleet_state = result['fleet_state'];
            this.state.flag = result['flag'];
            if (this.state.flag === 0) {
                this.state.manufacture_list = result['manufacture_list'];
                this.state.model_list = result['model_list'];
            } else {
                this.state.admin_odometer_list = result['admin_odometer_list'];
                this.state.admin_fleet_cost_list = result['admin_fleet_cost_list'];
                this.state.admin_recurring_list = result['admin_recurring_list'];
                this.state.fleet_vehicle_list = result['fleet_vehicle_list'];
                this.state.fleet_model_list = result['fleet_model_list'];
                this.state.fleet_manufacture_list = result['fleet_manufacture_list'];
            }
            this.lastChartData = {
                odometer: result['odometer_value_list'],
                serviceType: result['service_type'],
                serviceCost: result['service_cost_list']
            };
            this.renderCharts(
                result['odometer_value_list'],
                result['service_type'],
                result['service_cost_list']
            );
        } catch (e) {
            console.error('Fleet dashboard fetch error:', e);
        }
    }
}

FleetDashboard.template = 'fleet_advanced_dashboard.FleetDashBoard';
registry.category("actions").add("fleet_dashboard_tag", FleetDashboard);
