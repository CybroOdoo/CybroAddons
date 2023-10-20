/** @odoo-module */
import { loadBundle} from "@web/core/assets";
var AbstractAction = require('web.AbstractAction');
var core = require('web.core');
var QWeb = core.qweb;
/**
 * Custom dashboard component for the fleet rental application.
 */
var CustomDashBoard = AbstractAction.extend({
    template: 'CustomDashBoard',
    events: {
        'click button': 'onclick_dateSubmit_',
        'click #hide_modal': '_hideModal',
    },
    /**
     * Handles the click event of the date submit button.
     * event - The click event.
     */
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
                    method: 'vehicle_most_rented',
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
    /**
     * Hides the warning modal.
     */
    _hideModal: function() {
        this.$el.find('#modal_warning')
            .modal('hide')
    },
    init: function(parent, context) {
        this._super(parent, context);
        this.dashboards_templates = ['DashboardFleetRental'];
    },
    willStart: function() {
        var self = this;
        return $.when(loadBundle(this), this._super())
            .then(function() {
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
    /**
     * Renders the dashboard templates.
     */
    render_dashboards: function() {
        var self = this;
        _.each(this.dashboards_templates, function(template) {
            self.$el.find('.o_pj_dashboard')
                .append(QWeb.render(template, {
                    widget: self
                }));
        });
    },
    /**
     * Renders the graphs.
     */
    render_graphs: function() {
        var self = this;
        self.render_get_most_rended_cars();
    },
    /**
     * Fetches the data needed for the dashboard.
     * @returns {Promise} - A promise that resolves when the data is fetched.
     */
    fetch_data: async function() {
        var self = this;
        var def1 = await this._rpc({
                model: 'car.rental.contract',
                method: 'cars_availability'
            })
            .then(function(data) {
                self.available_cars = data['available_cars']
                self.running_cars = data['cars_running']
            })
        var def2 = await this._rpc({
                model: 'car.rental.contract',
                method: 'car_details'
            })
            .then(function(data) {
                self.running_vehicle_details = data['running_details']
            })
        var def2 = await this._rpc({
                model: 'car.rental.contract',
                method: 'car_details'
            })
            .then(function(data) {
                self.available_vehicle_details = data['available_cars']
            })
        var def3 = await this._rpc({
                model: 'car.rental.contract',
                method: 'top_customers'
            })
            .then(function(customers) {
                self.top_customers = customers
            })
    },

    /**
     * Renders the most rented cars graph.
     */
    render_get_most_rended_cars: function() {
        var self = this;
        var start_date = self.$el.find('#start_date')
            .val()
        var end_date = self.$el.find('#end_date')
            .val()
        var ctx = self.$el.find(".most_rented_cars")
        this._rpc({
                model: 'car.rental.contract',
                method: 'vehicle_most_rented',
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
})
core.action_registry.add('fleet_rental_dashboard', CustomDashBoard);
return CustomDashBoard
