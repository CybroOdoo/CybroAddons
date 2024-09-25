/** @odoo-module **/
import {Component,useState,useRef,onWillStart,onMounted} from "@odoo/owl";
import {registry} from "@web/core/registry";
import { jsonrpc } from "@web/core/network/rpc_service";
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
    async setup(){
        this.state = useState({
           flag:null,
           admin_odometer_list:[],
           admin_fleet_cost_list:[],
           admin_recurring_list:[],
           fleet_vehicle_list:[],
           fleet_model_list:[],
           fleet_manufacture_list:[],
           odometer_value:null,
           service_value:null,
           recurring_value:null,
           all_vehicles:null,
           fleet_state:[],
           manufacture_list:[],
           model_list:[],
           data: {
            "drivers": [],
            "vehicles": [],
            "manufactures": []
           }
        })
        this.filter = useRef("filters")
        this.fleet_main = useRef("fleet_main")
        this.action = useService("action");
        this.fetch_data();
        this.state.data = await this.render_filter();
    }
    /**
     * Handles filter change events and updates the dashboard data.
     */
    _onchangeFilter(){
        var self = this;
        jsonrpc('/fleet_advanced_dashboard/filter_data', {
            'data':{
                "date": this.filter.el.querySelector('#date_filter').value,
                'vehicle':this.filter.el.querySelector('#vehicle_selection').value,
                'driver':this.filter.el.querySelector('#driver_selection').value,
                'manufacturer':this.filter.el.querySelector('#manufacturers_selection').value
            }
        }).then(function(result){
            self.state.admin_odometer_list = result[3],
            self.state.admin_fleet_cost_list = result[4],
            self.state.admin_recurring_list = result[5],
            self.state.fleet_vehicle_list = result[6],
            self.state.fleet_model_list = result[7],
            self.state.fleet_manufacture_list=result[8],
            self.state.odometer_value=result[0],
            self.state.service_value=result[1],
            self.state.recurring_value=result[2]
        });
    }

    /**
     * Opens the Manufacturers view based on the current state.
     */
    _onClickManufacturers(){
        if (this.state.flag == 1) {
             this.OpenVehicleModelBrand(this.state.fleet_manufacture_list)
        }
        else{
            this.OpenVehicleModelBrand(this.state.fleet_manufacture_list)
        }
    }

    /**
     * Opens the vehicle model brand view with a specific domain.
     * @param {Array} domain - The domain to filter the records.
     */
    OpenVehicleModelBrand(domain){
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'Manufacturers',
            res_model: 'fleet.vehicle.model.brand',
            domain: [["id", "in", domain]],
            view_mode: 'kanban',
            views: [[false, 'kanban'],[false, 'form']],
            target: 'self'
        });
    }

    /**
     * Opens the Models view based on the current state.
     */
    _onClickModels(){
        if (this.state.flag == 1){
            this.OpenVehicleModel(this.state.fleet_model_list)
        }
        else{
            this.OpenVehicleModel(this.state.fleet_model_list)
        }
    }
    /**
     * Opens the vehicle model view with a specific domain.
     * @param {Array} domain - The domain to filter the records.
     */
    OpenVehicleModel(domain){
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'Models',
            res_model: 'fleet.vehicle.model',
            domain: [["id", "in", domain]],
            view_mode: 'kanban',
            views: [[false, 'kanban'],[false, 'form']],
            target: 'self'
        });
    }
    /**
     * Opens the Vehicles view based on the current state.
     */
    _onClickVehicles(){
        if (this.state.flag == 1) {
            this.action.doAction({
                type: 'ir.actions.act_window',
                name: 'Vehicles',
                res_model: 'fleet.vehicle',
                view_mode: 'kanban',
                views: [[false, 'kanban'],[false, 'form']],
                domain: [["id", "in", this.state.fleet_vehicle_list]],
                target: 'self'
            });
        }
    }
    /**
     * Opens the Contracts view based on the current state.
     */
    _onClickContracts() {
        if (this.state.flag == 1) {
             this.action.doAction({
                type: 'ir.actions.act_window',
                name: 'Vehicles',
                res_model: 'fleet.vehicle.log.contract',
                domain: [["id", "in", this.state.admin_recurring_list]],
                view_mode: 'kanban',
                views: [[false, 'list'],[false, 'form']],
                target: 'self'
            });
        }
    }
    /**
     * Opens the Services view based on the current state.
     */
    _onClickServices(){
        if (this.state.flag == 1) {
             this.action.doAction({
                type: 'ir.actions.act_window',
                name: 'Services',
                res_model: 'fleet.vehicle.log.services',
                domain: [["id", "in", this.state.admin_fleet_cost_list]],
                view_mode: 'list',
                views: [[false, 'list'],[false, 'form']],
                target: 'self'
             })
        }
    }
    /**
     * Opens the Odometers view based on the current state.
     */
    _onClickOdoMeter(){
        if (this.state.flag == true) {
            this.action.doAction({
                type: 'ir.actions.act_window',
                name: 'Odometers',
                res_model: 'fleet.vehicle.odometer',
                domain: [["id", "in", this.state.admin_odometer_list]],
                view_mode: 'list',
                views: [[false, 'list'],[false, 'form']],
                target: 'self'
            })
        }
    }
    /**
     * Fetches filter data for the dashboard.
     * @returns {Object} The filter data including drivers, vehicles, and manufactures.
     */
    async render_filter(){
        const { drivers, vehicles, manufactures } = await jsonrpc('/fleet/filter', {})
        return { drivers, vehicles, manufactures}
    }
    /**
     * Fetches data for the dashboard and draws charts.
     */
    fetch_data(){
        var self = this;
        var def1 = jsonrpc('/web/dataset/call_kw', {
            model: 'fleet.vehicle',
            method: 'get_tiles_data',
            args: [],
            kwargs: {}
        }).then(function(result) {
            self.state.odometer_value = result['total_odometer'],
            self.state.service_value = result['service_cost'],
            self.state.recurring_value = result['recurring_cost'],
            self.state.all_vehicles = result['all_vehicles'],
            self.state.fleet_state =  result['fleet_state'],
            self.state.flag = result['flag']
            if (self.state.flag == 0) {
                self.state.manufacture_list = result['manufacture_list'],
                self.state.model_list = result['model_list']
            }
            else{
                self.state.admin_odometer_list = result['admin_odometer_list'],
                self.state.admin_fleet_cost_list = result['admin_fleet_cost_list'],
                self.state.admin_recurring_list = result['admin_recurring_list'],
                self.state.fleet_vehicle_list = result['fleet_vehicle_list'],
                self.state.fleet_model_list = result['fleet_model_list'],
                self.state.fleet_manufacture_list = result['fleet_manufacture_list']
            }
            google.charts.load('current', {
                'packages': ['corechart']
            });
            google.charts.setOnLoadCallback(drawChart);
              function drawChart() {
                    try{
                        var data = google.visualization.arrayToDataTable(result['odometer_value_list']);
                         var options = {
                            title: 'Odometer Reading Monthly Wise',
                            hAxis: {title: 'Month'},
                            vAxis: {title: 'Odometer Values'},
                            legend: 'none',
                            pointsVisible: true,
                         }
                         var line_chart = new google.visualization.LineChart(self.fleet_main.el.querySelector('#lineChart'));
                         line_chart.draw(data, options);
                         var service_data = google.visualization.arrayToDataTable(result['service_type']);
                         var service_options = {
                            title: 'Service Types',
                            pieHole: 0.4
                        };
                        var service_chart = new google.visualization.PieChart(self.fleet_main.el.querySelector('#service_Chart'));
                        service_chart.draw(service_data, service_options);
                        var data = google.visualization.arrayToDataTable(result['service_cost_list']);
                        var options = {
                            title: ' Service Cost Last Six Months',
                            vAxis: {
                                gridlines: {color: 'transparent'},
                                title: 'Service Cost'
                            },
                            legend: 'none',
                        };
                        var chart = new google.visualization.ColumnChart(self.fleet_main.el.querySelector('#barChart'));
                        chart.draw(data, options);
                    }
                    catch (e) {
                        self.fetch_data();
                    }
              }
        });
        return $.when(def1);
    }
}

DashboardAction.template = "fleet_advanced_dashboard.FleetDashBoard"

registry.category("actions").add("dashboard_action", DashboardAction);
