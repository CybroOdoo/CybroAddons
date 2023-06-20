odoo.define('pj_dashboard.Dashboard', function(require) {
    "use strict";
    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var QWeb = core.qweb;
    var ajax = require('web.ajax');
    var rpc = require('web.rpc');
    var _t = core._t;
    var web_client = require('web.web_client');
    var ProjectDashboard = AbstractAction.extend({
        template: 'ProjectDashboard',
        events: {
            'click .tot_projects': 'tot_projects',
            'click .tot_tasks': 'tot_tasks',
            'click .tot_profitability': 'tot_profitability',
            'click .hr_recorded': 'hr_recorded',
            'click .tot_sale': 'tot_sale',
            'click .tot_emp': 'tot_emp',
            'change #start_date': '_onchangeFilter',
            'change #end_date': '_onchangeFilter',
            'change #employee_selection': '_onchangeFilter',
            'change #project_selection': '_onchangeFilter',
        },
        init: function(parent, context) {
            this._super(parent, context);
            this.dashboards_templates = ['DashboardProject', 'DashboardChart'];
            this.today_sale = [];
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
                self.render_dashboards();
                self.render_graphs();
                self.render_filter();
            });
        },
        /**
        rendering the dashboard
        */
        render_dashboards: function() {
            var self = this;
            _.each(this.dashboards_templates, function(template) {
                self.$('.o_pj_dashboard').append(QWeb.render(template, {
                    widget: self
                }));
            });
        },
        /**
        function for getting values to the filters
        */
        render_filter: function() {
            ajax.rpc('/project/filter').then(function(data) {
                var projects = data[0]
                var employees = data[1]
                $(projects).each(function(project) {
                    $('#project_selection').append("<option value=" + projects[project].id + ">" + projects[project].name + "</option>");
                });
                $(employees).each(function(employee) {
                    $('#employee_selection').append("<option value=" + employees[employee].id + ">" + employees[employee].name + "</option>");
                });
            })
        },
        /**
        function for getting values to the filters
        */
        _onchangeFilter: function() {
            this.flag = 1
            var start_date = $('#start_date').val();
            var end_date = $('#end_date').val();
            var self = this;
            if (!start_date) {
                start_date = "null"
            }
            if (!end_date) {
                end_date = "null"
            }
            var employee_selection = $('#employee_selection').val();
            var project_selection = $('#project_selection').val();
            ajax.rpc('/project/filter-apply', {
                'data': {
                    'start_date': start_date,
                    'end_date': end_date,
                    'project': project_selection,
                    'employee': employee_selection
                }
            }).then(function(data) {
                self.tot_hrs = data['list_hours_recorded']
                self.tot_employee = data['total_emp']
                self.tot_project = data['total_project']
                self.tot_task = data['total_task']
                self.tot_so = data['total_so']
                document.getElementById("tot_project").innerHTML = data['total_project'].length
                document.getElementById("tot_employee").innerHTML = data['total_emp'].length
                document.getElementById("tot_task").innerHTML = data['total_task'].length
                document.getElementById("tot_hrs").innerHTML = data['hours_recorded']
                document.getElementById("tot_margin").innerHTML = data['total_margin']
                document.getElementById("tot_so").innerHTML = data['total_so'].length
            })
        },
        /**
        rendering the graph
        */
        render_graphs: function() {
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
        /**
        function for getting values to project graph
        */
        render_project_task: function() {
            var self = this
            rpc.query({
                model: "project.project",
                method: "get_project_task_count",
            }).then(function(data) {
                var ctx = self.$("#project_doughnut");
                new Chart(ctx, {
                    type: "doughnut",
                    data: {
                        labels: data.project,
                        datasets: [{
                            backgroundColor: data.color,
                            data: data.task
                        }]
                    },
                    options: {
                        legend: {
                            position: 'left'
                        },
                        cutoutPercentage: 40,
                        responsive: true,
                    }
                });
            })
        },
        /**
        for opening project view
        */
        tot_projects: function(e) {
            var self = this;
            e.stopPropagation();
            e.preventDefault();
            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };
            if (this.flag == 0) {
                this.do_action({
                    name: _t("Projects"),
                    type: 'ir.actions.act_window',
                    res_model: 'project.project',
                    domain: [
                        ["id", "in", this.total_projects_ids]
                    ],
                    view_mode: 'kanban,form',
                    views: [
                        [false, 'kanban'],
                        [false, 'form']
                    ],
                    target: 'current'
                }, options)
            } else {
                if (this.tot_project) {
                    this.do_action({
                        name: _t("Projects"),
                        type: 'ir.actions.act_window',
                        res_model: 'project.project',
                        domain: [
                            ["id", "in", this.tot_project]
                        ],
                        view_mode: 'kanban,form',
                        views: [
                            [false, 'kanban'],
                            [false, 'form']
                        ],
                        target: 'current'
                    }, options)
                }
            }
        },
        /**
        for opening project task view
        */
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
                domain: [
                    ["id", "in", self.tot_task]
                ],
                view_mode: 'tree,kanban,form',
                views: [
                    [false, 'list'],
                    [false, 'form']
                ],
                target: 'current'
            }, options)
        },
        /**
        for opening margin view
        */
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
                res_model: 'project.project',
                view_mode: 'pivot',
                views: [
                    [false, 'pivot'],
                    [false, 'graph']
                ],
                target: 'current'
            }, options)
        },
        /**
        for opening account analytic line view
        */
        hr_recorded: function(e) {
            var self = this;
            e.stopPropagation();
            e.preventDefault();
            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };
            if (this.flag == 0) {
                this.do_action({
                    name: _t("Timesheets"),
                    type: 'ir.actions.act_window',
                    res_model: 'account.analytic.line',
                    view_mode: 'tree,form',
                    views: [
                        [false, 'list']
                    ],
                    target: 'current'
                }, options)
            } else {
                if (this.tot_hrs) {
                    this.do_action({
                        name: _t("Timesheets"),
                        type: 'ir.actions.act_window',
                        res_model: 'account.analytic.line',
                        domain: [
                            ["id", "in", this.tot_hrs]
                        ],
                        view_mode: 'tree,form',
                        views: [
                            [false, 'list']
                        ],
                        target: 'current'
                    }, options)
                }
            }
        },
        /**
        for opening sale order view
        */
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
                domain: [
                    ["id", "in", this.tot_so]
                ],
                view_mode: 'tree,form',
                views: [
                    [false, 'list'],
                    [false, 'form']
                ],
                target: 'current'
            }, options)
        },
        /**
        for opening total hr employee view
        */
        tot_emp: function(e) {
            var self = this;
            e.stopPropagation();
            e.preventDefault();
            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };
            if (this.flag == 0) {
                this.do_action({
                    name: _t("Employees"),
                    type: 'ir.actions.act_window',
                    res_model: 'hr.employee',
                    view_mode: 'tree,form',
                    views: [
                        [false, 'list'],
                        [false, 'form']
                    ],
                    target: 'current'
                }, options)
            } else {
                this.do_action({
                    name: _t("Employees"),
                    type: 'ir.actions.act_window',
                    res_model: 'hr.employee',
                    domain: [
                        ["id", "in", this.tot_employee]
                    ],
                    view_mode: 'tree,form',
                    views: [
                        [false, 'list'],
                        [false, 'form']
                    ],
                    target: 'current'
                }, options)

            }
        },
        /**
        function for getting values to employee graph
        */
        render_top_employees_graph: function() {
            var self = this
            var ctx = self.$(".top_selling_employees");
            rpc.query({
                model: "project.project",
                method: 'get_top_timesheet_employees',
            }).then(function(arrays) {
                var data = {
                    labels: arrays[1],
                    datasets: [{
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
                        display: false,
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
                    type: 'bar',
                    data: data,
                    options: options
                });

            });
        },
        /**
        function for getting values when page is loaded
        */
        fetch_data: function() {
            this.flag = 0
            var self = this;
            var def1 = this._rpc({
                model: 'project.project',
                method: 'get_tiles_data'
            }).then(function(result) {
                if (result['flag'] == 1) {
                    self.total_projects = result['total_projects']
                    self.total_tasks = result['total_tasks']
                    self.tot_task = result['total_tasks_ids']
                    self.total_hours = result['total_hours']
                    self.total_profitability = result['total_profitability']
                    self.total_employees = result['total_employees']
                    self.total_sale_orders = result['total_sale_orders']
                    self.project_stage_list = result['project_stage_list']
                    self.tot_so = result['sale_orders_ids']
                    self.flag_user = result['flag']
                    self.total_projects_ids = result['total_projects_ids']
                } else {
                    self.tot_task = result['total_tasks_ids']
                    self.total_projects = result['total_projects']
                    self.total_tasks = result['total_tasks']
                    self.total_hours = result['total_hours']
                    self.total_sale_orders = result['total_sale_orders']
                    self.project_stage_list = result['project_stage_list']
                    self.flag_user = result['flag']
                    self.tot_so = result['sale_orders_ids']
                    self.total_projects_ids = result['total_projects_ids']
                }
            });
            /**
            function for getting values to hours table
            */
            var def3 = self._rpc({
                    model: "project.project",
                    method: "get_hours_data",
                })
                .then(function(res) {
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
                .then(function(res) {
                    self.task_data = res['project'];
                });
            return $.when(def1, def3, def4);
        },
    });
    core.action_registry.add('project_dashboard', ProjectDashboard);
    return ProjectDashboard;
});