/** @odoo-module */
import {loadBundle} from "@web/core/assets";

var AbstractAction = require('web.AbstractAction');
var core = require('web.core');
var QWeb = core.qweb;
var rpc = require('web.rpc');
var CustomDashBoard = AbstractAction.extend({
    template: 'CustomDashBoard',
    events: {
        'click select[name="period"]': 'onclick_period_selection',
    },


    init: function(parent, context) {
        this._super(parent, context);
        this.dashboards_templates = ['DashboardLabourSupply'];
        this.labour_supply_details = [];
    },
    willStart: function() {
        var self = this;
        return $.when(loadBundle(this), this._super()).then(function() {
            return self.fetch_data();
        });
    },
    start: function() {
        var self = this;
        this.set("title", 'Dashboard');
        return this._super().then(function() {
            self.render_dashboards();
            self.render_graphs();
        });
    },
    render_dashboards: function() {
        var self = this;
        _.each(this.dashboards_templates, function(template) {
            self.$('.o_pj_dashboard').append(QWeb.render(template, {
                widget: self
            }));
        });
    },
    render_graphs: function() {
        var self = this;
        self.render_get_workers_count();
        self.render_get_contract_count_state();
        self.render_get_contract_count_customer();
        self.render_get_contract_amount();
    },
    fetch_data: function() {
        var self = this;
        var def1 = this._rpc({
             // function to get  labour contract details for dashboard
            model: 'workers.details',
            method: 'get_labour_supply_details'
        }).then(function(result) {
            self.labour_supply_details = result['ongoing_contract']
        });
        var def2 = this._rpc({
            // function to get  top costumer for dashboard
            model: 'workers.details',
            method: 'get_top_customer'
        }).then(function(result) {
            self.customers = result['customer']
        });
        var def3 = this._rpc({
            // function to get  total invoice amount for dashboard
            model: 'workers.details',
            method: 'get_total_invoiced_amount'
        }).then(function(result) {
            self.total_invoiced_amount = result['invoiced_amount']
        });
        var def4 = this._rpc({
            // function to get  skills available for dashboard
            model: 'workers.details',
            method: 'get_skills_available'
        }).then(function(result) {
            self.skills = result['skill']
        });
        var def5 = this._rpc({
            // function to get  total expected amount for dashboard
            model: 'workers.details',
            method: 'get_expected_amount'
        }).then(function(result) {
            self.expected_amount = result['expected_amount']
        });
        var def6 = this._rpc({
            // function to get  workers available for dashboard
            model: 'workers.details',
            method: 'get_workers_available'
        }).then(function(result) {
            self.workers = result['workers']
        });
        return $.when(def1, def2, def3, def4, def5, def6);
    },
    render_get_workers_count: function() {
        // function to get  workers count for dashboard
        var self = this
        var ctx = self.$(".worker_availability");
        this._rpc({
            model: "workers.details",
            method: "get_workers_count",
        }).then(function(arrays) {
            var data = {
                labels: arrays.state,
                datasets: [{
                    label: "Workers",
                    data: arrays.count,
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
                    display: true,
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
                            display: false,
                        },
                        ticks: {
                            min: 0,
                            display: false,
                        }
                    }]
                }
            };

            //create Chart class object
            var chart = new Chart(ctx, {
                type: "doughnut",
                data: data,
                options: options
            });
        });
    },

    render_get_contract_count_state: function() {
        // function to get  labour supply count for dashboard on the basis of state

        var self = this
        var ctx = self.$(".contract");
        this._rpc({
            model: "workers.details",
            method: "get_contract_count_state",
        }).then(function(arrays) {
            var data = {
                labels: arrays.state,
                datasets: [{
                    label: "Hide",
                    data: arrays.count,
                    backgroundColor: '#003f5c',
                    borderColor: '#003f5c',
                    barPercentage: 0.5,
                    barThickness: 6,
                    maxBarThickness: 8,
                    minBarLength: 0,
                    borderWidth: 1, // Specify bar border width
                    type: 'line', // Set this data to a line chart
                    fill: false,
                    borderWidth: 1
                }, ]
            };

            //options
            var options = {
                responsive: true,
                title: false,
                legend: {
                    display: true,
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
                        }
                    }]
                }
            };

            //create Chart class object
            var chart = new Chart(ctx, {
                type: "line",
                data: data,
                options: options
            });
        });
    },
    render_get_contract_count_customer: function() {
        // function to get  labour supply count for dashboard on the basis of customer

        var self = this
        var ctx = self.$(".customer_contract");
        this._rpc({
            model: "workers.details",
            method: "get_contract_count_customer",
        }).then(function(arrays) {
            var data = {
                labels: arrays.name,
                datasets: [{
                    label: "Hide",
                    data: arrays.count,
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
                    display: true,
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
        });
    },
    render_get_contract_amount: function() {
        // function to get  labour supply amount for dashboard on the basis of state

        var self = this
        var ctx = self.$(".labour_contract");
        this._rpc({
            model: "workers.details",
            method: "get_contract_amount",
        }).then(function(arrays) {
            var data = {
                labels: arrays.sequence,
                datasets: [{
                    label: "Hide",
                    data: arrays.amount,
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
                    display: true,
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
        });
    },
    onclick_period_selection: function(events) {
        // function to get  labour supply amount for dashboard on the basis of filter

        var option = $(events.target).val();
        var self = this;
        this._rpc({
            model: "workers.details",
            method: "get_details_amount",
            args: [option]
        }).then(function(array) {
            var ctx = self.$(".labour_contract");
            var data = {
                labels: array.sequence,
                datasets: [{
                    label: "Hide",
                    data: array.amount,
                    backgroundColor: [
                        "#665193",
                        "#ff7c43",
                        "#ffa600",
                        "#a05195",
                        "#2f4b7c",
                        "#f95d6a",
                        "#6d5c16",
                        "#003f5c",
                        "#013f5c",
                        "#d45087"
                    ],
                    borderColor: [
                        "#003f5c",
                        "#2f4b7c",
                        "#f95d6a",
                        "#665191",
                        "#d45087",
                        "#003f5c",
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
                    display: true,
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

        });
    },
})
core.action_registry.add('labour_supply_dashboard', CustomDashBoard);
return CustomDashBoard;
