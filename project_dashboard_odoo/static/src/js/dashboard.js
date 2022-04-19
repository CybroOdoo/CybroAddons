odoo.define('pj_dashboard.Dashboard', function (require) {
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




var PjDashboard = AbstractAction.extend({
    template:'PjDashboard',
    cssLibs: [
        '/project_dashboard_odoo/static/src/css/lib/nv.d3.css'
    ],
    jsLibs: [
        '/project_dashboard_odoo/static/src/js/lib/d3.min.js'
    ],

    events: {
             'click .tot_projects':'tot_projects',
             'click .tot_tasks':'tot_tasks',
             'click .tot_profitability':'tot_profitability',
             'click .hr_recorded':'hr_recorded',
             'click .tot_sale':'tot_sale',
             'click .tot_emp':'tot_emp',
             'click #income_this_year': 'onclick_income_this_year',
             'click #income_last_year': 'onclick_income_last_year',
             'click #income_this_month': 'onclick_income_this_month',

        },

    init: function(parent, context) {
        this._super(parent, context);
        this.dashboards_templates = ['DashboardProject','DashboardChart'];
        this.today_sale = [];
    },


    willStart: function() {
        var self = this;
        return $.when(ajax.loadLibs(this), this._super()).then(function() {
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

    render_dashboards: function(){
        var self = this;
        _.each(this.dashboards_templates, function(template) {
                self.$('.o_pj_dashboard').append(QWeb.render(template, {widget: self}));
            });
    },



    render_graphs: function(){
        var self = this;
            self.render_project_task();
            self.render_top_employees_graph();

    },

    on_reverse_breadcrumb: function() {
        var self = this;
        web_client.do_push_state({});
        this.fetch_data().then(function() {
            self.$('.o_pj_dashboard').empty();
            self.render_dashboards();
            self.render_graphs();
        });
    },

//
    onclick_toggle_two: function(ev) {
        this.onclick_income_this_year(ev);
        this.onclick_income_last_year(ev);
        this.onclick_income_this_month(ev);
    },




    render_project_task:function(){
        var self = this;
        var w = 400;
        var h = 400;
        var r = h/2;
        var elem = this.$('.emp_graph');
        var colors = ['#70cac1', '#659d4e', '#208cc2', '#4d6cb1', '#584999', '#8e559e', '#cf3650', '#f65337', '#fe7139',
        '#ffa433', '#ffc25b', '#f8e54b'];
        var color = d3.scale.ordinal().range(colors);
        rpc.query({
            model: "project.project",
            method: "get_project_task",
        }).then(function (data) {
            var segColor = {};
            var vis = d3.select(elem[0]).append("svg:svg").data([data]).attr("width", w).attr("height", h).append("svg:g").attr("transform", "translate(" + r + "," + r + ")");
            var pie = d3.layout.pie().value(function(d){return d.value;});
            var arc = d3.svg.arc().outerRadius(r);
            var arcs = vis.selectAll("g.slice").data(pie).enter().append("svg:g").attr("class", "slice");
            arcs.append("svg:path")
                .attr("fill", function(d, i){
                    return color(i);
                })
                .attr("d", function (d) {
                    return arc(d);
                });

            var legend = d3.select(elem[0]).append("table").attr('class','legend');

            var tr = legend.append("tbody").selectAll("tr").data(data).enter().append("tr");

            tr.append("td").append("svg").attr("width", '16').attr("height", '16').append("rect")
                .attr("width", '16').attr("height", '16')
                .attr("fill",function(d, i){ return color(i) });

            tr.append("td").text(function(d){ return d.label;});

            tr.append("td").attr("class",'legendFreq')
                .text(function(d){ return d.value;});



        });

    },



    //project
        tot_projects: function(e) {
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        this.do_action({
            name: _t("Projects"),
            type: 'ir.actions.act_window',
            res_model: 'project.project',
            view_mode: 'kanban,form',
            views: [[false, 'list'],[false, 'form']],
            target: 'current'
        }, options)
    },

    //task
        tot_tasks: function(e) {
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        this.do_action({
            name: _t("Tasks"),
            type: 'ir.actions.act_window',
            res_model: 'project.task',
            view_mode: 'tree,kanban,form',
            views: [[false, 'list'],[false, 'form']],
            target: 'current'
        }, options)
    },

    //task
        tot_profitability: function(e) {
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        this.do_action({
            name: _t("Profitability"),
            type: 'ir.actions.act_window',
            res_model: 'project.profitability.report',
            view_mode: 'pivot',
            views: [[false, 'pivot'],[false, 'graph']],
            target: 'current'
        }, options)
    },

    //hr timesheets

        hr_recorded: function(e) {
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        this.do_action({
            name: _t("Timesheets"),
            type: 'ir.actions.act_window',
            res_model: 'account.analytic.line',
            view_mode: 'tree,form',
            views: [[false, 'list']],
//            domain: [['project_id', '!=',self.project_id ]],
            target: 'current'
        }, options)
    },

    //total saleorder

        tot_sale: function(e) {
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        this.do_action({
            name: _t("Sale Order"),
            type: 'ir.actions.act_window',
            res_model: 'sale.order',
            view_mode: 'tree',
            views: [[false, 'list']],
            domain: [['analytic_account_id', '!=',self.analytic_account_id ]],
            target: 'current'
        }, options)
    },

    //total emp

        tot_emp: function(e) {
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        this.do_action({
            name: _t("Employees"),
            type: 'ir.actions.act_window',
            res_model: 'hr.employee',
            view_mode: 'tree,form',
            views: [[false, 'list'],[false, 'form']],
//            domain: [['project_id', '!=',self.project_id ]],
            target: 'current'
        }, options)
    },



    render_top_employees_graph:function(){
       var self = this
        var ctx = self.$(".top_selling_employees");
            rpc.query({
                model: "project.project",
                method: "get_top_timesheet_employees",
            }).then(function (arrays) {


          var data = {
            labels: arrays[1],
            datasets: [
              {
                label: "Hours Spent",
                data: arrays[0],
                backgroundColor: [
                  "rgba(190, 27, 75,1)",
                  "rgba(31, 241, 91,1)",
                  "rgba(103, 23, 252,1)",
                  "rgba(158, 106, 198,1)",
                  "rgba(250, 217, 105,1)",
                  "rgba(255, 98, 31,1)",
                  "rgba(255, 31, 188,1)",
                  "rgba(75, 192, 192,1)",
                  "rgba(153, 102, 255,1)",
                  "rgba(10,20,30,1)"
                ],
                borderColor: [
                 "rgba(190, 27, 75, 0.2)",
                 "rgba(190, 223, 122, 0.2)",
                 "rgba(103, 23, 252, 0.2)",
                  "rgba(158, 106, 198, 0.2)",
                  "rgba(250, 217, 105, 0.2)",
                  "rgba(255, 98, 31, 0.2)",
                  "rgba(255, 31, 188, 0.2)",
                  "rgba(75, 192, 192, 0.2)",
                  "rgba(153, 102, 255, 0.2)",
                  "rgba(10,20,30,0.3)"
                ],
                borderWidth: 1
              },

            ]
          };

  //options
          var options = {
            responsive: true,
            title: {
              display: true,
              position: "top",
              text: " Time by Employees",
              fontSize: 18,
              fontColor: "#111"
            },
            legend: {
              display: true,
              position: "bottom",
              labels: {
                fontColor: "#333",
                fontSize: 16
              }
            },
            scales: {
              yAxes: [{
                ticks: {
                  min: 0
                }
              }]
            }
          };

          //create Chart class object
          var chart = new Chart(ctx, {
            type: "horizontalBar",
            data: data,
            options: options
          });

        });
        },

    onclick_income_last_year: function(ev) {
        ev.preventDefault();
        var selected = $('.btn.btn-tool.income');
        var data = $(selected[0]).data();
        var posted = 1;

        rpc.query({
                model: 'project.project',
                method: 'get_income_last_year',
                args: [],
            })
            .then(function(result) {

                $('#net_profit_current_months').hide();
                $('#net_profit_last_year').show();
                $('#net_profit_this_year').hide();

                var ctx = document.getElementById("canvas").getContext('2d');

                // Define the data

                var profit = result.profit;

                var labels = result.month; // Add labels to array
                // End Defining data

                // End Defining data
                if (window.myCharts != undefined)
                    window.myCharts.destroy();
                window.myCharts = new Chart(ctx, {
                    //var myChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: labels,
                        datasets: [
                      {
                                label: 'Profitability', // Name the series
                                data: profit, // Specify the data values array
                                backgroundColor: '#0bd465',
                                borderColor: '#0bd465',

                                borderWidth: 1, // Specify bar border width
                                type: 'line', // Set this data to a line chart
                                fill: false
                            }
                        ]
                    },
                    options: {
                        responsive: true, // Instruct chart js to respond nicely.
                        maintainAspectRatio: false, // Add to prevent default behaviour of full-width/height
                    }
                });

            })
    },

    onclick_income_this_year: function(ev) {
        ev.preventDefault();
        var selected = $('.btn.btn-tool.income');
        var data = $(selected[0]).data();
        var posted = false;

        rpc.query({
                model: 'project.project',
                method: 'get_income_this_year',
                args: [],

            })
            .then(function(result) {

                $('#net_profit_current_months').hide();
                $('#net_profit_last_year').hide();
                $('#net_profit_this_year').show();

                var ctx = document.getElementById("canvas").getContext('2d');

                // Define the data
                var income = result.income; // Add data values to array
//                    var expense = result.expense;
                var profit = result.profit;

                var labels = result.month; // Add labels to array


                if (window.myCharts != undefined)
                    window.myCharts.destroy();
                window.myCharts = new Chart(ctx, {
                    //var myChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: labels,
                        datasets: [
                            {
                                label: 'Profitability', // Name the series
                                data: profit, // Specify the data values array
                                backgroundColor: '#0bd465',
                                borderColor: '#0bd465',

                                borderWidth: 1, // Specify bar border width
                                type: 'line', // Set this data to a line chart
                                fill: false
                            }
                        ]
                    },
                    options: {
                        responsive: true, // Instruct chart js to respond nicely.
                        maintainAspectRatio: false, // Add to prevent default behaviour of full-width/height
                    }
                });

            })
    },

    onclick_income_this_month: function(ev) {
        ev.preventDefault();
        var selected = $('.btn.btn-tool.income');
        var data = $(selected[0]).data();
        var posted = 1;

        rpc.query({
                model: 'project.project',
                method: 'get_income_this_month',
                args: [],

            })
            .then(function(result) {


                var ctx = document.getElementById("canvas").getContext('2d');

                // Define the data
                var profit = result.profit;

                var labels = result.date; // Add labels to array
                // End Defining data

                // End Defining data
                if (window.myCharts != undefined)
                    window.myCharts.destroy();
                window.myCharts = new Chart(ctx, {
                    //var myChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: labels,
                        datasets: [

                            {
                                label: 'Profitability', // Name the series
                                data: profit, // Specify the data values array
                                backgroundColor: '#0bd465',
                                borderColor: '#0bd465',

                                borderWidth: 1, // Specify bar border width
                                type: 'line', // Set this data to a line chart
                                fill: false
                            }
                        ]
                    },
                    options: {
                        responsive: true, // Instruct chart js to respond nicely.
                        maintainAspectRatio: false, // Add to prevent default behaviour of full-width/height
                    }
                });

            })
    },


    fetch_data: function() {
        var self = this;
        var def1 =  this._rpc({
                model: 'project.project',
                method: 'get_tiles_data'
    }).then(function(result)
     {
       self.total_projects = result['total_projects'],
       self.total_tasks = result['total_tasks'],
       self.total_hours = result['total_hours'],
       self.total_profitability = result['total_profitability'],
       self.total_employees = result['total_employees'],
       self.total_sale_orders = result['total_sale_orders']

    });
    var def2 = self._rpc({
            model: "project.project",
            method: "get_details",
        })
        .then(function (res) {
            self.invoiced = res['invoiced'];
            self.to_invoice = res['to_invoice'];
            self.time_cost = res['time_cost'];
            self.expen_cost = res['expen_cost'];
            self.payment_details = res['payment_details'];
        });
        var def3 = self._rpc({
            model: "project.project",
            method: "get_hours_data",
        })
        .then(function (res) {
            self.hour_recorded = res['hour_recorded'];
            self.hour_recorde = res['hour_recorde'];
            self.billable_fix = res['billable_fix'];
            self.non_billable = res['non_billable'];
            self.total_hr = res['total_hr'];
        });

        var def4 = self._rpc({
            model: "project.project",
            method: "get_task_data",
        })
        .then(function (res) {
            self.task_data = res['project'];

        });

        return $.when(def1,def2,def3,def4);
    },

});

core.action_registry.add('project_dashboard', PjDashboard);

return PjDashboard;

});

