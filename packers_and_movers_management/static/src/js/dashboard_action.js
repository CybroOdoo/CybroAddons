/** @odoo-module */
import { loadBundle } from "@web/core/assets";
var AbstractAction = require('web.AbstractAction');
var ajax = require('web.ajax');
var core = require('web.core');
var QWeb = core.qweb;
var rpc = require('web.rpc');
var CustomDashBoard = AbstractAction.extend({
// Extended abstract class to create dashboard
    template: 'CustomDashBoard',
    events: {
        'change #stock_selection': function(e) {
                e.stopPropagation();
                var value = $(e.target).val();
                if (value=="year"){
                    this.onclick_this_year(value);
                }else if (value=="day"){
                    this.onclick_this_day(value);
                }else if (value=="month"){
                    this.onclick_this_month(value);
                }else if (value=="week"){
                    this.onclick_this_week(value);
                }
            },
        },
    init: function(parent, context) {
    //Function to Initializes all the values while loading the file
       this._super(parent, context);
       this.dashboards_templates = ['DashboardTruckBooking'];
       this.booking_count = []
       this.distance_count = []
       this.total_invoice = []
       this.total_amount = []
    },
     willStart: function() {// Returns the function fetch_data when page load.
       var self = this;
       return Promise.all([ajax.loadLibs(this), this._super()]).then(function() {
           return self.fetch_data();
       });
     },
    start: function() {
    //Fetch data and return render_dashboards and render_graph function
        self = this;
        this.set("title", 'Dashboard');
        return this._super().then(function() {
            self.render_dashboards();
            self.render_graph();
        });
    },
    render_dashboards: function() {//Return value to show in tile.
        self = this;
        _.each(this.dashboards_templates, function(template) {
            self.$('.o_pj_dashboard').append(QWeb.render(template, {widget: self}));
        });
    },
    fetch_data: function() {
    //Function to call rpc query to fetch data fom python
       self = this;
       var def1 =  this._rpc({
           model: 'truck.booking',
           method: 'get_total_booking'
       }).then(function(result)
        {
          self.booking_count = result.total_booking,
          self.distance_count = result.total_distance_count,
          self.total_invoice = result.total_invoice
          self.total_amount = result.total_amount
        });
       var def2 =  this._rpc({
               model: 'truck.booking',
               method: 'get_top_truck'
       }).then(function(result)
        {
        self.truck = result['truck']
        self.customer = result['customer']
        self.upcoming = result['upcoming']
   });
       return $.when(def1,def2);
   },
    render_graph: function(){//Add function to load in dashboard.
       this.render_booking();
       this.render_truck();
       this.render_distance();
       this.render_weight();
       },
    render_booking:function(){
    //Function to add booking chart on the basis of customer
        rpc.query({
            model: "truck.booking",
            method: "get_booking_analysis",
        }).then(function (result) {
            new Chart(self.$("#booking"), {
                type: 'bar',
                data: {
                    labels: result.name,
                    datasets: [{
                        label: 'Count',
                        data: result.count,
                        backgroundColor: [
                            "#003f5c",
                            "#2f4b7c",
                            "#f95d6a",
                            "#665191",
                            "#d45087",
                            "#ff7c43",
                            "#ffa600",
                            "#a05195",
                            "#6d5c16",
                            "#CCCCFF"

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
                            "#6d5c16",
                            "#CCCCFF"
                        ],
                        barPercentage: 0.5,
                        barThickness: 6,
                        maxBarThickness: 8,
                        minBarLength: 0,
                        borderWidth: 1,
                        type: 'bar',
                        fill: false
                    }]
                },
                options: {
                    scales: {
                        y: {
                            beginAtZero: true
                        },
                    },
                }
            });
        });
    },
    render_truck:function(){
    //Function to add booking chart on the basis of truck
        rpc.query({
            model: "truck.booking",
            method: "get_truck_analysis",
        }).then(function (result) {
            new Chart(self.$("#truck"), {
                type: 'doughnut',
                data: {
                    labels: result.name,
                    datasets: [{
                        label: 'Count',
                        data: result.count,
                        backgroundColor: [
                            "#665191",
                            "#ff7c43",
                            "#ffa600",
                            "#d45087",
                            "#a05195",
                            "#6d5c16",
                            "#CCCCFF",
                            "#003f5c",
                            "#2f4b7c",
                            "#f95d6a",

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
                            "#6d5c16",
                            "#CCCCFF"
                        ],
                        barPercentage: 0.5,
                        barThickness: 6,
                        maxBarThickness: 8,
                        minBarLength: 0,
                        borderWidth: 1,
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
                }
            });
        });
    },
    render_distance:function(){
    //Function to add total distance chart on the basis of customer and truck
        rpc.query({
            model: "truck.booking",
            method: "get_distance",
        }).then(function (result) {
            new Chart(self.$("#cust_distance"), {
                type: 'doughnut',
                data: {
                    labels: result.cust,
                    datasets: [{
                        label: 'Count',
                        data: result.cust_sum,
                        backgroundColor: [
                            "#665191",
                            "#ff7c43",
                            "#ffa600",
                            "#d45087",
                            "#a05195",
                            "#6d5c16",
                            "#CCCCFF",
                            "#003f5c",
                            "#2f4b7c",
                            "#f95d6a",

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
                            "#6d5c16",
                            "#CCCCFF"
                        ],
                        barPercentage: 0.5,
                        barThickness: 6,
                        maxBarThickness: 8,
                        minBarLength: 0,
                        borderWidth: 1,
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
                }
            });
            new Chart(self.$("#truck_distance"), {
                        type: 'line',
                    data: {
                        labels: result.truck_name,//x axis
                        datasets: [{
                            label: 'count', // Name the series
                            data: result.truck_sum,
                            backgroundColor: '#003f5c',
                            borderColor: '#003f5c',
                            barPercentage: 0.5,
                            barThickness: 6,
                            maxBarThickness: 8,
                            minBarLength: 0,
                            borderWidth: 1, // Specify bar border width
                            type: 'line', // Set this data to a line chart
                            fill: false
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true
                            },
                        },
                    }
                    });
        });
    },
    render_weight:function(){
    //Function to add total goods weight chart on the basis of customer and truck
        rpc.query({
            model: "truck.booking",
            method: "get_weight",
        }).then(function (result) {
             new Chart(self.$("#cust_weight"), {
                        type: 'line',
                    data: {
                        labels: result.cust,//x axis
                        datasets: [{
                            label: 'count', // Name the series
                            data: result.cust_sum,
                            backgroundColor: '#003f5c',
                            borderColor: '#003f5c',
                            barPercentage: 0.5,
                            barThickness: 6,
                            maxBarThickness: 8,
                            minBarLength: 0,
                            borderWidth: 1, // Specify bar border width
                            type: 'line', // Set this data to a line chart
                            fill: false
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true
                            },
                        },
                    }
                    });
             new Chart(self.$("#truck_weight"), {
                type: 'bar',
                data: {
                    labels: result.truck_name,
                    datasets: [{
                        label: 'Count',
                        data: result.truck_sum,
                        backgroundColor: [
                            "#003f5c",
                            "#2f4b7c",
                            "#f95d6a",
                            "#665191",
                            "#d45087",
                            "#ff7c43",
                            "#ffa600",
                            "#a05195",
                            "#6d5c16",
                            "#CCCCFF"

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
                            "#6d5c16",
                            "#CCCCFF"
                        ],
                        barPercentage: 0.5,
                        barThickness: 6,
                        maxBarThickness: 8,
                        minBarLength: 0,
                        borderWidth: 1,
                        type: 'bar',
                        fill: false
                    }]
                },
                options: {
                    scales: {
                        y: {
                            beginAtZero: true
                        },
                    },
                }
            });

        });
    },
    onclick_this_year: function (ev) {//Function shows a year filtered dashboard
            self = this;
            rpc.query({
                model: 'truck.booking',
                method: 'get_select_filter',
                args: [ev],
            })
            .then(function (result) {
                self.$('#booking_this_day').hide();
                self.$('#distance_this_day').hide();
                self.$('#amount_this_day').hide();
                self.$('#invoice_this_day').hide();
                self.$('#booking_this_month').hide();
                self.$('#distance_this_month').hide();
                self.$('#amount_this_month').hide();
                self.$('#invoice_this_month').hide();
                self.$('#booking_this_week').hide();
                self.$('#distance_this_week').hide();
                self.$('#amount_this_week').hide();
                self.$('#invoice_this_week').hide();
                self.$('.total').hide();
                self.$('#booking_this_year').show();
                self.$('#distance_this_year').show();
                self.$('#amount_this_year').show();
                self.$('#invoice_this_year').show();
                self.$('#booking_this_year').empty();
                self.$('#distance_this_year').empty();
                self.$('#amount_this_year').empty();
                self.$('#invoice_this_year').empty();
                self.$('#booking_this_year').append('<span>' + result['booking'][0]['count'] + '</span>');
                self.$('#distance_this_year').append('<span>' + result['distance'][0]['sum'] + '</span>');
                self.$('#amount_this_year').append('<span>' + result['amount'][0]['sum'] + '</span>');
                self.$('#invoice_this_year').append('<span>' + result['invoice'][0]['sum'] + '</span>');
                self.get_cust_invoice(result);
                self.get_truck_invoice(result);
                self.get_cust_distance(result);
                self.get_truc_distance(result);
                self.get_cust_weight(result);
                self.get_truck_weight(result);
            })
        },
    onclick_this_day: function (ev) {//Function shows day filtered dashboard.
            self = this;
            rpc.query({
               model: 'truck.booking',
                method: 'get_select_filter',
                args: [ev],
            })
            .then(function (result) {
                self.$('.total').hide();
                self.$('#booking_this_month').hide();
                self.$('#distance_this_month').hide();
                self.$('#amount_this_month').hide();
                self.$('#invoice_this_month').hide();
                self.$('#booking_this_week').hide();
                self.$('#distance_this_week').hide();
                self.$('#amount_this_week').hide();
                self.$('#invoice_this_week').hide();
                self.$('#booking_this_year').hide();
                self.$('#distance_this_year').hide();
                self.$('#amount_this_year').hide();
                self.$('#invoice_this_year').hide();
                self.$('#booking_this_day').show();
                self.$('#distance_this_day').show();
                self.$('#amount_this_day').show();
                self.$('#invoice_this_day').show();
                self.$('#booking_this_day').empty();
                self.$('#distance_this_day').empty();
                self.$('#amount_this_day').empty();
                self.$('#invoice_this_day').empty();
                self.$('#booking_this_day').append('<span>' + result['booking'][0]['count'] + '</span>');
                self.$('#distance_this_day').append('<span>' + result['distance'][0]['sum'] + '</span>');
                self.$('#amount_this_day').append('<span>' + result['amount'][0]['sum'] + '</span>');
                self.$('#invoice_this_day').append('<span>' + result['invoice'][0]['sum'] + '</span>');
                self.get_cust_invoice(result);
                self.get_truck_invoice(result);
                self.get_cust_distance(result);
                self.get_truc_distance(result);
                self.get_cust_weight(result);
                self.get_truck_weight(result);
            })
        },
    onclick_this_week: function (ev) {//Function shows week filtered dashboard.
            self = this;
            rpc.query({
               model: 'truck.booking',
                method: 'get_select_filter',
                args: [ev],
            })
            .then(function (result) {

                self.$('.total').hide();
                self.$('#booking_this_month').hide();
                self.$('#distance_this_month').hide();
                self.$('#amount_this_month').hide();
                self.$('#invoice_this_month').hide();
                self.$('#booking_this_year').hide();
                self.$('#distance_this_year').hide();
                self.$('#amount_this_year').hide();
                self.$('#invoice_this_year').hide();
                self.$('#booking_this_day').hide();
                self.$('#distance_this_day').hide();
                self.$('#amount_this_day').hide();
                self.$('#invoice_this_day').hide();

                self.$('#booking_this_week').show();
                self.$('#distance_this_week').show();
                self.$('#amount_this_week').show();
                self.$('#invoice_this_week').show();

                self.$('#booking_this_week').empty();
                self.$('#distance_this_week').empty();
                self.$('#amount_this_week').empty();
                self.$('#invoice_this_week').empty();

                self.$('#booking_this_week').append('<span>' + result['booking'][0]['count'] + '</span>');
                self.$('#distance_this_week').append('<span>' + result['distance'][0]['sum'] + '</span>');
                self.$('#amount_this_week').append('<span>' + result['amount'][0]['sum'] + '</span>');
                self.$('#invoice_this_week').append('<span>' + result['invoice'][0]['sum'] + '</span>');
                self.get_cust_invoice(result);
                self.get_truck_invoice(result);
                self.get_cust_distance(result);
                self.get_truc_distance(result);
                self.get_cust_weight(result);
                self.get_truck_weight(result);
            })
        },
    onclick_this_month: function (ev) {//Function shows month filtered dashboard.
            self = this;
            rpc.query({
               model: 'truck.booking',
                method: 'get_select_filter',
                args: [ev],
            })
            .then(function (result) {
                self.$('.total').hide();
                self.$('#booking_this_year').hide();
                self.$('#distance_this_year').hide();
                self.$('#amount_this_year').hide();
                self.$('#invoice_this_year').hide();
                self.$('#booking_this_day').hide();
                self.$('#distance_this_day').hide();
                self.$('#amount_this_day').hide();
                self.$('#invoice_this_day').hide();
                self.$('#booking_this_week').hide();
                self.$('#distance_this_week').hide();
                self.$('#amount_this_week').hide();
                self.$('#invoice_this_week').hide();
                self.$('#booking_this_month').show();
                self.$('#distance_this_month').show();
                self.$('#amount_this_month').show();
                self.$('#invoice_this_month').show();
                self.$('#booking_this_month').empty();
                self.$('#distance_this_month').empty();
                self.$('#amount_this_month').empty();
                self.$('#invoice_this_month').empty();
                self.$('#booking_this_month').append('<span>' + result['booking'][0]['count'] + '</span>');
                self.$('#distance_this_month').append('<span>' + result['distance'][0]['sum'] + '</span>');
                self.$('#amount_this_month').append('<span>' + result['amount'][0]['sum'] + '</span>');
                self.$('#invoice_this_month').append('<span>' + result['invoice'][0]['sum'] + '</span>');
                self.get_cust_invoice(result);
                self.get_truck_invoice(result);
                self.get_cust_distance(result);
                self.get_truc_distance(result);
                self.get_cust_weight(result);
                self.get_truck_weight(result);
            })
        },
    get_cust_invoice: function (result) {
    //Function to create a chart which shows the total invoice according to the customer
        new Chart(self.$("#booking"), {
                    type: 'bar',
                    data: {
                        labels: result.cust_invoice_name,
                        datasets: [{
                            label: 'Count',
                            data: result.cust_invoice_sum,
                            backgroundColor: [
                                "#003f5c",
                                "#2f4b7c",
                                "#f95d6a",
                                "#665191",
                                "#d45087",
                                "#ff7c43",
                                "#ffa600",
                                "#a05195",
                                "#6d5c16",
                                "#CCCCFF"

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
                                "#6d5c16",
                                "#CCCCFF"
                            ],
                            barPercentage: 0.5,
                            barThickness: 6,
                            maxBarThickness: 8,
                            minBarLength: 0,
                            borderWidth: 1,
                            type: 'bar',
                            fill: false
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true
                            },
                        },
                    }
                });
    },
    get_truck_invoice: function (result){//Function to create a chart which shows the total invoice according to the truck.
        new Chart(self.$("#truck"), {
                type: 'doughnut',
                data: {
                    labels: result.truck_invoice_name,
                    datasets: [{
                        label: 'Count',
                        data: result.truck_invoice_count,
                        backgroundColor: [
                            "#665191",
                            "#ff7c43",
                            "#ffa600",
                            "#d45087",
                            "#a05195",
                            "#6d5c16",
                            "#CCCCFF",
                            "#003f5c",
                            "#2f4b7c",
                            "#f95d6a",

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
                            "#6d5c16",
                            "#CCCCFF"
                        ],
                        barPercentage: 0.5,
                        barThickness: 6,
                        maxBarThickness: 8,
                        minBarLength: 0,
                        borderWidth: 1,
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
                }
            });
    },
    get_cust_distance: function (result){//Function to create a graph which shows the distance according to the customer
        new Chart(self.$("#cust_distance"), {
                type: 'doughnut',
                data: {
                    labels: result.cust_distance_name,
                    datasets: [{
                        label: 'Count',
                        data: result.cust_distance_count,
                        backgroundColor: [
                            "#665191",
                            "#ff7c43",
                            "#ffa600",
                            "#d45087",
                            "#a05195",
                            "#6d5c16",
                            "#CCCCFF",
                            "#003f5c",
                            "#2f4b7c",
                            "#f95d6a",

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
                            "#6d5c16",
                            "#CCCCFF"
                        ],
                        barPercentage: 0.5,
                        barThickness: 6,
                        maxBarThickness: 8,
                        minBarLength: 0,
                        borderWidth: 1,
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
                }
            });
    },
    get_truc_distance: function (result){//Function to create a graph which shows the distance according to the truck
        new Chart(self.$("#truck_distance"), {
                        type: 'line',
                    data: {
                        labels: result.truck_distance_name,//x axis
                        datasets: [{
                            label: 'count', // Name the series
                            data: result.truck_distance_count, // Specify the data values array
                            backgroundColor: '#003f5c',
                            borderColor: '#003f5c',
                            barPercentage: 0.5,
                            barThickness: 6,
                            maxBarThickness: 8,
                            minBarLength: 0,
                            borderWidth: 1, // Specify bar border width
                            type: 'line', // Set this data to a line chart
                            fill: false
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true
                            },
                        },
                    }
                    });
    },
    get_cust_weight: function (result){//Function to create a chart which shows the total goods weight according to the customer
        new Chart(self.$("#cust_weight"), {
                        type: 'line',
                    data: {
                        labels: result.cust_weight_name,//x axis
                        datasets: [{
                            label: 'count', // Name the series
                            data: result.cust_weight_count, // Specify the data values array
                            backgroundColor: '#003f5c',
                            borderColor: '#003f5c',
                            barPercentage: 0.5,
                            barThickness: 6,
                            maxBarThickness: 8,
                            minBarLength: 0,
                            borderWidth: 1, // Specify bar border width
                            type: 'line', // Set this data to a line chart
                            fill: false
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true
                            },
                        },
                    }
                    });
    },
    get_truck_weight: function (result){//Function to create a chart which shows the total goods weight according to the truck
        new Chart(self.$("#truck_weight"), {
                type: 'bar',
                data: {
                    labels: result.truck_weight_name,
                    datasets: [{
                        label: 'Count',
                        data: result.truck_weight_count,
                        backgroundColor: [
                            "#003f5c",
                            "#2f4b7c",
                            "#f95d6a",
                            "#665191",
                            "#d45087",
                            "#ff7c43",
                            "#ffa600",
                            "#a05195",
                            "#6d5c16",
                            "#CCCCFF"

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
                            "#6d5c16",
                            "#CCCCFF"
                        ],
                        barPercentage: 0.5,
                        barThickness: 6,
                        maxBarThickness: 8,
                        minBarLength: 0,
                        borderWidth: 1,
                        type: 'bar',
                        fill: false
                    }]
                },
                options: {
                    scales: {
                        y: {
                            beginAtZero: true
                        },
                    },
                }
            });
    },
})
core.action_registry.add('dashboard_tags', CustomDashBoard);
return CustomDashBoard;
