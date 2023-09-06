/** @odoo-module */
import { loadBundle } from "@web/core/assets";
var AbstractAction = require('web.AbstractAction');
var core = require('web.core');
var QWeb = core.qweb;
var rpc = require('web.rpc');
var CustomDashBoard = AbstractAction.extend({// Extended abstract class to create dashboard
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
    init: function(parent, context) {//function to Initializes all the values while loading the file
       this._super(parent, context);
       this.dashboards_templates = ['DashboardVenueBooking'];
       this.booking_count = []
       this.total_invoice = []
       this.total_amount = []
       this.total_venue = []
    },
     willStart: function() {// returns the function fetch_data when page load.
       var self = this;
       return $.when(loadBundle(this), this._super()).then(function() {
           return self.fetch_data();
       });
     },
    start: function() {//fetch data and return render_dashboards and render_graph function
        self = this;
        this.set("title", 'Dashboard');
        return this._super().then(function() {
            self.render_dashboards();
            self.render_graph();
        });
    },
    render_dashboards: function() {//return value to show in tile.
        self = this;
        _.each(this.dashboards_templates, function(template) {
            self.$('.o_pj_dashboard').append(QWeb.render(template, {widget: self}));
        });
    },
    fetch_data: function() {//function to call rpc query to fetch data fom python
       self = this;
       var def1 =  this._rpc({
           model: 'venue.booking',
           method: 'get_total_booking'
       }).then(function(result)
        {
          self.booking_count = result.total_booking,
          self.total_invoice = result.total_invoice
          self.total_amount = result.total_amount
          self.total_venue = result.total_venue
        });
       var def2 =  this._rpc({
               model: 'venue.booking',
               method: 'get_top_venue'
       }).then(function(result)
        {
        self.venue = result['venue']
        self.customer = result['customer']
        self.upcoming = result['upcoming']
   });
       return $.when(def1,def2);
   },
    render_graph: function(){//Add function to load in dashboard.
       this.render_booking();
       this.render_venue();
       },
    render_booking:function(){//Function to add booking chart on the basis of customer
        rpc.query({
            model: "venue.booking",
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
                    responsive: true,
                    maintainAspectRatio: false,
                }
            });
        });
    },
    render_venue:function(){//Function to add booking chart on the basis of venue
        rpc.query({
            model: "venue.booking",
            method: "get_venue_analysis",
        }).then(function (result) {
            new Chart(self.$("#venue"), {
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
                    responsive: true,
                    maintainAspectRatio: false,
                }
            });
        });
    },

    onclick_this_year: function (ev) {//Function shows a year filtered dashboard
            self = this;
            rpc.query({
                model: 'venue.booking',
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
                self.get_venue_invoice(result);
            })
        },
    onclick_this_day: function (ev) {//Function shows day filtered dashboard.
            self = this;
            rpc.query({
               model: 'venue.booking',
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
                self.get_venue_invoice(result);
            })
        },
    onclick_this_week: function (ev) {//Function shows week filtered dashboard.
            self = this;
            rpc.query({
               model: 'venue.booking',
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
                self.get_venue_invoice(result);
            })
        },
    onclick_this_month: function (ev) {//Function shows month filtered dashboard.
            self = this;
            rpc.query({
               model: 'venue.booking',
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
                self.get_venue_invoice(result);
            })
        },
    get_cust_invoice: function (result) {//function to create a chart which shows the total invoice according to the customer
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
                        responsive: true,
                        maintainAspectRatio: false,
                    }
                });
    },
    get_venue_invoice: function (result){//function to create a chart which shows the total invoice according to the truck.
        new Chart(self.$("#venue"), {
                type: 'doughnut',
                data: {
                    labels: result.venue_invoice_name,
                    datasets: [{
                        label: 'Count',
                        data: result.venue_invoice_count,
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
                    responsive: true,
                    maintainAspectRatio: false,
                }
            });
    },

})
core.action_registry.add('dashboard_tags', CustomDashBoard);
return CustomDashBoard;
