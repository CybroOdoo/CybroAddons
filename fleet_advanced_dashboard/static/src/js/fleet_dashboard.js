odoo.define('fleet_advanced_dashboard.dashboard_action', function(require) {
    "use strict";
    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var QWeb = core.qweb;
    var ajax = require('web.ajax');
    var FleetDashBoard = AbstractAction.extend({
        template: 'FleetDashBoard',
        events: {
            'click #fleet_manufacturers': '_onClickManufacturers',
            'click #fleet_models': '_onClickModels',
            'click #fleet_vehicles': '_onClickVehicles',
            'click #fleet_contracts': '_onClickContracts',
            'click #fleet_odometer': '_onClickOdoMeter',
            'click #fleet_services': '_onClickServices',
            'change #driver_selection': '_onchangeFilter',
            'change #vehicle_selection': '_onchangeFilter',
            'change #date_filter': '_onchangeFilter',
            'change #manufacturers_selection': '_onchangeFilter',
        },
        /**
         * Getting data after filtration
         */
        _onchangeFilter: function() {
            var self = this;
            ajax.jsonRpc('/fleet_advanced_dashboard/filter_data', 'call', {'data': {
                'date': self.$el.find('#date_filter').val(),
                'vehicle': self.$el.find('#vehicle_selection').val(),
                'driver': self.$el.find('#driver_selection').val(),
                'manufacturer': self.$el.find('#manufacturers_selection').val()
            }}).then(function(result) {
                self.admin_odometer_list = result[3]
                self.admin_fleet_cost_list = result[4]
                self.admin_recurring_list = result[5]
                self.fleet_vehicle_list = result[6]
                self.fleet_model_list = result[7]
                self.fleet_manufacture_list = result[8]
                self.$el.find('#odometer_value').html(result[0]);
                self.$el.find('#odometer_value2').html(result[0]);
                self.$el.find('#service_value').html(result[1]);
                self.$el.find('#service_value2').html(result[1]);
                self.$el.find('#recurring_value').html(result[2]);
                self.$el.find('#recurring_value2').html(result[2]);
            })
        },
        /**
        * Checking whether the filter is applied or not
        */
        _onClickManufacturers: function() {
            if (this.flag == 0) {
                this.OpenVehicleModelBrand(this.manufacture_list)
            } else {
                this.OpenVehicleModelBrand(this.fleet_manufacture_list)
            }
        },
        /**
         * Opening "fleet.vehicle.model.brand" kanban view
         */
        OpenVehicleModelBrand: function(domain){
            this.do_action({
                type: 'ir.actions.act_window',
                name: 'Manufacturers',
                res_model: 'fleet.vehicle.model.brand',
                domain: [["id", "in", domain]],
                view_mode: 'kanban',
                views: [[false, 'kanban'],[false, 'form']],
                target: 'self'
            });
        },
        /**
         * Checking whether the filter is applied or not
         */
        _onClickModels: function() {
            if (this.flag == 0){
                this.OpenVehicleModel(this.model_list)
            } else {
                this.OpenVehicleModel(this.fleet_model_list)
            }
        },
        /**
         * Opening "fleet.vehicle.model" kanban view
         */
        OpenVehicleModel: function(domain){
            this.do_action({
                type: 'ir.actions.act_window',
                name: 'Models',
                res_model: 'fleet.vehicle.model',
                domain: [["id", "in", domain]],
                view_mode: 'kanban',
                views: [[false, 'kanban'],[false, 'form']],
                target: 'self'
            });
        },
        /**
         * Opening "fleet.vehicle" kanban view
         */
        _onClickVehicles: function() {
            if (this.flag == 1) {
                this.do_action({
                    type: 'ir.actions.act_window',
                    name: 'Vehicles',
                    res_model: 'fleet.vehicle',
                    view_mode: 'kanban',
                    views: [[false, 'kanban'],[false, 'form']],
                    domain: [["id", "in", this.fleet_vehicle_list]],
                    target: 'self'
                });
            }
        },
        /**
         * Opening "fleet.vehicle.log.contract" list view
         */
        _onClickContracts: function() {
            if (this.flag == 1) {
                this.do_action({
                    type: 'ir.actions.act_window',
                    name: 'Vehicles',
                    res_model: 'fleet.vehicle.log.contract',
                    domain: [["id", "in", this.admin_recurring_list]],
                    view_mode: 'kanban',
                    views: [[false, 'list'],[false, 'form']],
                    target: 'self'
                });
            }
        },
        /**
         * Opening "fleet.vehicle.log.services" list view
         */
        _onClickServices: function() {
            if (this.flag == 1) {
                this.do_action({
                    type: 'ir.actions.act_window',
                    name: 'Services',
                    res_model: 'fleet.vehicle.log.services',
                    domain: [["id", "in", this.admin_fleet_cost_list]],
                    view_mode: 'list',
                    views: [[false, 'list'],[false, 'form']],
                    target: 'self'
                });
            }
        },
        /**
         * Opening "fleet.vehicle.odometer" list view
         */
        _onClickOdoMeter: function() {
            if (this.flag == 1) {
                this.do_action({
                    type: 'ir.actions.act_window',
                    name: 'Odometers',
                    res_model: 'fleet.vehicle.odometer',
                    domain: [["id", "in", this.admin_odometer_list]],
                    view_mode: 'list',
                    views: [[false, 'list'],[false, 'form']],
                    target: 'self'
                });
            }
        },
        init: function(parent, context) {
            this._super(parent, context);
            this.dashboards_templates = ['FleetDashBoard'];
        },
        willStart: function() {
            var self = this;
            return $.when(this._super()).then(function() {
                return self.fetch_data();
            });
        },
        start: function() {
            var self = this;
            this.set("title", 'Dashboard');
            return this._super().then(function() {
                self.render_filter();
                self.render_dashboards();
            });
        },
        /**
         * Appending values to the template
         */
        render_dashboards: function() {
            var self = this;
            _.each(this.dashboards_templates, function(template) {
                self.$('.fleet_oh_dashboards').append(QWeb.render(template, {
                    widget: self
                }));
            });
        },
        /**
         * Getting data to selection field
         */
        render_filter: function() {
            var self = this;
            ajax.rpc('/fleet/filter').then(function(data) {
                var drivers = data[0]
                var vehicles = data[1]
                var manufacturers = data[2]
                for (var i = 0; i < vehicles.length; i++) {
                    self.$el.find('#vehicle_selection').append("<option value=" + vehicles[i].id + " style='background-color:#827c93;'>" + vehicles[i].name + "</option>");
                }
                for (var i = 0; i < drivers.length; i++) {
                    self.$el.find('#driver_selection').append("<option value=" + drivers[i].id + " style='background-color:#827c93;'>" + drivers[i].name + "</option>");
                }
                for (var i = 0; i <manufacturers.length; i++) {
                    self.$el.find('#manufacturers_selection').append("<option value=" + manufacturers[i].id + " style='background-color:#827c93;'>" + manufacturers[i].name + "</option>");
                }
            })
        },
        /**
         * Getting data to the window
         */
        fetch_data: function() {
            var self = this;
            var def1 = this._rpc({
                model: 'fleet.vehicle',
                method: 'get_tiles_data'
            }).then(function(result) {
                self.total_odometer = result['total_odometer']
                self.service_cost = result['service_cost']
                self.recurring_cost = result['recurring_cost']
                self.all_vehicles = result['all_vehicles']
                self.fleet_state = result['fleet_state']
                self.flag = result['flag']
                if (self.flag == 0) {
                    self.manufacture_list = result['manufacture_list']
                    self.model_list = result['model_list']
                } else {
                    self.admin_odometer_list = result['admin_odometer_list']
                    self.admin_fleet_cost_list = result['admin_fleet_cost_list']
                    self.admin_recurring_list = result['admin_recurring_list']
                    self.fleet_vehicle_list = result['fleet_vehicle_list']
                    self.fleet_model_list = result['fleet_model_list']
                    self.fleet_manufacture_list = result['fleet_manufacture_list']
                }
                google.charts.load('current', {
                    'packages': ['corechart']
                });
                google.charts.setOnLoadCallback(drawChart);
                //Function for drawing chart
                function drawChart() {
                    try {
                        var data = google.visualization.arrayToDataTable(result['odometer_value_list']);
                        var options = {
                            title: 'Odometer Reading Monthly Wise',
                            hAxis: {title: 'Month'},
                            vAxis: {title: 'Odometer Values'},
                            legend: 'none',
                            pointsVisible: true,
                        };
                        var line_chart = new google.visualization.LineChart(self.el.querySelector('#lineChart'));
                        line_chart.draw(data, options);
                        var service_data = google.visualization.arrayToDataTable(result['service_type']);
                        var service_options = {
                            title: 'Service Types',
                            pieHole: 0.4
                        };
                        var service_chart = new google.visualization.PieChart(self.el.querySelector('#service_Chart'));
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
                        var chart = new google.visualization.ColumnChart(self.el.querySelector('#barChart'));
                        chart.draw(data, options);
                    } catch (e) {
                        self.fetch_data();
                    }
                }
            });
            return $.when(def1);
        },
    })
    core.action_registry.add('fleet_advanced_dashboard_tags', FleetDashBoard);
    return FleetDashBoard;
})
