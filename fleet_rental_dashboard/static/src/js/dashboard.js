odoo.define('fleet_rental_dashboard.Dashboard', function(require) {
    "use strict";

    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var QWeb = core.qweb;
    var ajax = require('web.ajax');
    var rpc = require('web.rpc');
    var _t = core._t;
    var session = require('web.session');
    var web_client = require('web.web_client');
    var abstractView = require('web.AbstractView');
    var flag = 0;
    var tot_so = []
    var tot_project = []
    var tot_task = []
    var tot_employee = []
    var tot_hrs = []
    var tot_margin = []
    var CustomDashBoard = AbstractAction.extend({
        template: 'CustomDashBoard',
        // Define events
        events: {
            'click button': 'onclick_dateSubmit_',
            'click #hide_modal': '_hideModal',
        },
        // Constructor
        init: function(parent, context) {
            this._super(parent, context);
            this.dashboards_templates = ['DashboardFleetRental'];
        },
        willStart: function() {
            var self = this;
            return $.when(ajax.loadLibs(this), this._super()).then(function() {
                return self.fetch_data();
            });
        },
        start: function() {
            var self = this;
            this.set("title", 'Dashboard')
            return this._super()
                .then(function() {
                    self.render_dashboards();
                    self.render_graphs();
                })

        },
        _hideModal: function() {
        this.$el.find('#modal_warning')
            .modal('hide')
        },
        // Handle date submission
        onclick_dateSubmit_: function(event) {
            event.preventDefault()
            var start_date = this.$el.find('#start_date')
                .val()
            var end_date = this.$el.find('#end_date')
                .val()
            if (start_date > end_date) {
                this.$el.find('#modal_warning')
                    .modal('show')
            } else {
                var self = this;
                self.$el.find(".most_rented_cars")
                    .remove()
                self.$el.find(".most_rented_cars_pie")
                    .remove()
                self.$el.find(".most_rented_cars_line")
                    .remove()
                self.$el.find(".bar_canvas")
                    .append("<canvas class='most_rented_cars'/>")
                self.$el.find(".pie_canvas")
                    .append("<canvas class='most_rented_cars_pie'/>")
                self.$el.find(".line_canvas")
                    .append("<canvas class='most_rented_cars_line'/>")
                var ctx = self.$el.find(".most_rented_cars")
                this._rpc({
                        model: 'car.rental.contract',
                        method: 'get_vehicle_most_rented',
                        args: [start_date, end_date]
                    })
                    .then(function(cars) {
                        var data = {
                            labels: cars.name,
                            datasets: [{
                                data: cars.num,
                                fill: false,
                                backgroundColor: '#003f5c',
                                borderColor: '#003f5c',
                                barPercentage: 0.5,
                                barThickness: 6,
                                maxBarThickness: 8,
                                minBarLength: 0,
                                borderWidth: 1,
                                backgroundColor: [
                                    "#665191",
                                    "#ff7c43",
                                    "#ffa600",
                                    "#a05195",
                                    "#2f4b7c",
                                    "#f95d6a",
                                    "#6d5c16",
                                    "#003f5c",
                                    "#d45087"
                                ],
                                borderColor: [
                                    "#003f5c",
                                    "#2f4b7c",
                                    "#f95d6a",
                                    "#665191",
                                    "#d45087",
                                    "#ff7c43",
                                    "#ffa600",
                                    "#a05195",
                                    "#6d5c16"
                                ],
                                borderWidth: 1
                            }, ]
                        };
                        //options
                        var options = {
                            responsive: true,
                            title: true,
                            legend: {
                                display: false,
                                position: "right",
                                labels: {
                                    fontColor: "#333",
                                    fontSize: 16
                                }
                            },
                            scales: {
                                yAxes: [{
                                    gridLines: {
                                        color: "rgba(1, 0, 0, 0)",
                                        display: true,
                                    },
                                    ticks: {
                                        min: 0,
                                        display: true,
                                        stepSize: 1,
                                    }
                                }]
                            }
                        };
                        //create Chart class object
                        var chart = new Chart(ctx, {
                            type: "bar",
                            data: data,
                            options: options
                        });
                        var pie = self.$el.find(".most_rented_cars_pie")
                        var pie_chart = new Chart(pie, {
                            type: "doughnut",
                            data: data,
                        })
                        var line = self.$el.find(".most_rented_cars_line")
                        var line_chart = new Chart(line, {
                            type: "line",
                            data: data,
                        })
                    })
            }
        },
        render_dashboards: function() {
            var self = this;
            _.each(this.dashboards_templates, function(template) {
                self.$el.find('.o_pj_dashboard')
                    .append(QWeb.render(template, {
                        widget: self
                    }));
            });
        },
        render_graphs: function() {
            var self = this;
            self.render_get_most_rended_cars();
        },
        // Fetch data asynchronously
        fetch_data: async function() {
            var self = this;
            var def1 = await this._rpc({
                    model: 'car.rental.contract',
                    method: 'get_cars_availability'
                })
                .then(function(data) {
                    self.available_cars = data['available_cars']
                    self.running_cars = data['cars_running']
                })
            var def2 = await this._rpc({
                    model: 'car.rental.contract',
                    method: 'get_car_details'
                })
                .then(function(data) {
                    self.running_vehicle_details = data['running_details']
                })
            var def2 = await this._rpc({
                    model: 'car.rental.contract',
                    method: 'get_car_details'
                })
                .then(function(data) {
                    self.available_vehicle_details = data['available_cars']
                })
            var def3 = await this._rpc({
                    model: 'car.rental.contract',
                    method: 'get_top_customers'
                })
                .then(function(customers) {
                    self.top_customers = customers
                })
        },
        render_get_most_rended_cars: function() {
            var self = this;
            var start_date = self.$el.find('#start_date')
                .val()
            var end_date = self.$el.find('#end_date')
                .val()
            var ctx = self.$el.find(".most_rented_cars")
            this._rpc({
                    model: 'car.rental.contract',
                    method: 'get_vehicle_most_rented',
                    args: [start_date, end_date]
                })
                .then(function(cars) {
                    var data = {
                        labels: cars.name,
                        datasets: [{
                            data: cars.num,
                            fill: false,
                            backgroundColor: '#003f5c',
                            borderColor: '#003f5c',
                            barPercentage: 0.5,
                            barThickness: 6,
                            maxBarThickness: 8,
                            minBarLength: 0,
                            borderWidth: 1,
                            backgroundColor: [
                                "#665191",
                                "#ff7c43",
                                "#ffa600",
                                "#a05195",
                                "#2f4b7c",
                                "#f95d6a",
                                "#6d5c16",
                                "#003f5c",
                                "#d45087"
                            ],
                            borderColor: [
                                "#003f5c",
                                "#2f4b7c",
                                "#f95d6a",
                                "#665191",
                                "#d45087",
                                "#ff7c43",
                                "#ffa600",
                                "#a05195",
                                "#6d5c16"
                            ],
                            borderWidth: 1
                        }, ]
                    };
                    //options
                    var options = {
                        responsive: true,
                        title: false,
                        legend: {
                            display: false,
                            position: "right",
                            labels: {
                                fontColor: "#333",
                                fontSize: 16
                            }
                        },
                        scales: {
                            yAxes: [{
                                gridLines: {
                                    color: "rgba(1, 0, 0, 0)",
                                    display: true,
                                },
                                ticks: {
                                    min: 0,
                                    display: true,
                                    stepSize: 1,
                                }
                            }]
                        }
                    };
                    //create Chart class object
                    var chart = new Chart(ctx, {
                        type: "bar",
                        data: data,
                        options: options
                    });
                    var pie = self.$el.find(".most_rented_cars_pie")
                    var pie_chart = new Chart(pie, {
                        type: "doughnut",
                        data: data,
                    })
                    var line = self.$el.find(".most_rented_cars_line")
                    var line_chart = new Chart(line, {
                        type: "line",
                        data: data,
                    })
                })
        }
    });

    core.action_registry.add('fleet_rental_dashboard', CustomDashBoard);
    return CustomDashBoard;
});
