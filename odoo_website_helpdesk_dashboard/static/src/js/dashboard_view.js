odoo.define("odoo_website_helpdesk_dashboard.dashboard_view", function (require) {
    "use strict";
    // Import required modules
    const AbstractAction = require("web.AbstractAction");
    const core = require("web.core");
    const rpc = require("web.rpc");
    var ajax = require("web.ajax");
    // Get translation function
    const _t = core._t;
    const QWeb = core.qweb;
    // Define the Dashboard class extending AbstractAction
    const DashBoard = AbstractAction.extend({
        template: "HelpDesk_Dashboard",
        // Define event handlers
        events: {
            "click .inbox_tickets": "tickets_inbox",
            "click .inprogress_tickets": "tickets_inprogress",
            "click .done_tickets": "tickets_done",
            "click .team_card": "helpdesk_teams"
        },
        // Initialize the Dashboard class
        init: function (parent, context) {
            this._super(parent, context);
            this.dashboards_templates = ['DashBoardHelpDesk'];
        },
        // Start the Dashboard
        start: function () {
            var self = this;
            this.set("title", 'Dashboard');
            return this._super().then(function () {
                self.render_dashboards();
                self.render_graphs();
                self.$el.parent().addClass('oe_background_grey');
            });
        },
        // Render graphs on the dashboard
        render_graphs: function () {
            var self = this;
            self.render_tickets_month_graph();
            self.render_team_ticket_count_graph();
            self.render_projects_ticket_graph();
            self.render_billed_task_team_graph();
            self.render_team_ticket_done_graph();
        },
        // Render a doughnut chart for ticket counts by month
        render_tickets_month_graph: function () {
            var self = this
            var ctx = self.$(".ticket_month");
            rpc.query({
                model: "help.ticket",
                method: "get_ticket_month_pie",
            }).then(function (arrays) {
                var data = {
                    labels: arrays[1],
                    datasets: [{
                        label: "",
                        data: arrays[0],
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
                    },]
                };
                //Options
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
                                color: "rgba(0, 0, 0, 0)",
                                display: false,
                            },
                            ticks: {
                                min: 0,
                                display: false,
                            }
                        }]
                    }
                };
                //Create Chart class object
                var chart = new Chart(ctx, {
                    type: "doughnut",
                    data: data,
                    options: options
                });
            });
        },
        // Render a bar chart for ticket counts by team
        render_team_ticket_count_graph: function () {
            var self = this
            var ctx = self.$(".team_ticket_count");
            rpc.query({
                model: "help.ticket",
                method: "get_team_ticket_count_pie",
            }).then(function (arrays) {
                var data = {
                    labels: arrays[1],
                    datasets: [{
                        label: "",
                        data: arrays[0],
                        backgroundColor: [
                            'rgba(255, 99, 132, 0.2)',
                            'rgba(255, 159, 64, 0.2)',
                            'rgba(255, 205, 86, 0.2)',
                            'rgba(75, 192, 192, 0.2)',
                            'rgba(54, 162, 235, 0.2)',
                            'rgba(153, 102, 255, 0.2)',
                            'rgba(201, 203, 207, 0.2)'
                        ],
                        borderColor: ['rgb(255, 99, 132)',
                            'rgb(255, 159, 64)',
                            'rgb(255, 205, 86)',
                            'rgb(75, 192, 192)',
                            'rgb(54, 162, 235)',
                            'rgb(153, 102, 255)',
                            'rgb(201, 203, 207)'
                        ],
                        borderWidth: 1
                    },]
                };
                //Options
                var options = {
                    responsive: true,
                    title: false,
                    maintainAspectRatio: true,
                    legend: {
                        display: false //This will do the task
                    },
                    scales: {
                        yAxes: [{
                            display: true,
                            ticks: {
                                beginAtZero: true,
                                steps: 10,
                                stepValue: 5,
                                // max: 100
                            }
                        }]
                    }
                };
                //Create Chart class object
                var chart = new Chart(ctx, {
                    type: "bar",
                    data: data,
                    options: options
                });
            });
        },
        // Render a bar chart for ticket counts by project
        render_projects_ticket_graph: function () {
            var self = this
            var ctx = self.$(".projects_ticket");
            rpc.query({
                model: "help.ticket",
                method: "get_project_ticket_count",
            }).then(function (arrays) {
                var data = {
                    labels: arrays[1],
                    datasets: [{
                        label: "",
                        data: arrays[0],
                        backgroundColor: [
                            "rgba(175,180,255,0.75)",
                            "rgba(133,208,255,0.9)",
                            "rgba(113,255,221,0.79)",
                            "rgba(255,187,95,0.77)",
                            "#2c7fb8",
                            "#fa9fb5",
                            "#2f4b7c",
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
                    },]
                };
                  //Options
                var options = {
                    responsive: true,
                    title: false,
                    maintainAspectRatio: true,
                    legend: {
                        display: false //This will do the task
                    },
                    scales: {
                        yAxes: [{
                            display: true,
                            ticks: {
                                beginAtZero: true,
                                steps: 10,
                                stepValue: 5,
                                // max: 100
                            }
                        }]
                    }
                };
                //Create Chart class object
                var chart = new Chart(ctx, {
                    type: "bar",
                    data: data,
                    options: options
                });
            });
        },
        // Render a polar area chart for billed tasks by team
        render_billed_task_team_graph: function () {
            var self = this
            var ctx = self.$(".billed_team");
            rpc.query({
                model: "help.ticket",
                method: "get_billed_task_team_chart",
            }).then(function (arrays) {
                var data = {
                    labels: arrays[1],
                    datasets: [{
                        label: "",
                        data: arrays[0],
                        backgroundColor: [
                            "#a07fcd",
                            "#fea84c",
                            "#2cb8b1",
                            "#fa9fb5",
                            "#2f4b7c",
                            "#2c7fb8"
                        ],
                        borderColor: [
                            "#4fc9ff",
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
                    },]
                };
                //Options
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
                                color: "rgba(0, 0, 0, 0)",
                                display: false,
                            },
                            ticks: {
                                min: 0,
                                display: false,
                            }
                        }]
                    }
                };
                //Create Chart class object
                var chart = new Chart(ctx, {
                    type: "polarArea",
                    data: data,
                    options: options
                });
            });
        },
        // Render a line chart for ticket counts by team (done tickets)
        render_team_ticket_done_graph: function () {
            var self = this
            var ctx = self.$(".team_ticket_done");
            rpc.query({
                model: "help.ticket",
                method: "get_team_ticket_done_pie",
            }).then(function (arrays) {
                var data = {
                    labels: arrays[1],
                    datasets: [{
                        fill: false,
                        label: "",
                        data: arrays[0],
                        backgroundColor:[
                            "#b7c1ff",
                            "#6159ff",
                            "#c79bff",
                            "#0095b2"
                        ],
                        borderColor:
                            'rgba(54,162,235,0.49)'
                        ,
                        borderWidth: 2
                    },]
                };
                //Options
                var options = {
                    responsive: true,
                    title: false,
                    maintainAspectRatio: true,
                    legend: {
                        display: false //This will do the task
                    },
                    scales: {
                        yAxes: [{
                            display: true,
                            ticks: {
                                beginAtZero: true,
                                steps: 10,
                                stepValue: 5,
                                // max: 100
                            }
                        }]
                    }
                };
                //Create Chart class object
                var chart = new Chart(ctx, {
                    type: "line",
                    data: data,
                    options: options
                });
            });
        },
        // Render dashboard templates
        render_dashboards: function () {
            var self = this;
            var templates = ['DashBoardHelpDesk'];
            _.each(templates, function (template) {
                self.$('.helpdesk_dashboard_main').append(QWeb.render(template, {widget: self}));
            });
            rpc.query({
                model: "help.ticket",
                method: "get_tickets_count",
                args: [],
            }).then(function (result) {
                    $("#inbox_count").append("<span class='stat-digit'>" + result.inbox_count + "</span>");
                    $("#inprogress_count").append("<span class='stat-digit'>" + result.progress_count + "</span>");
                    $("#done_count").append("<span class='stat-digit'>" + result.done_count + "</span>");
                    $("#team_count").append("<span class='stat-digit'>" + result.team_count + "</span>");
                    ajax.jsonRpc("/help/tickets", "call", {}).then(function (values) {
                        $('.pending_tickets').append(values);
                    });
                });
        },
        // Event handler for clicking the inbox tickets
        tickets_inbox: function (ev) {
            var self = this;
            ev.stopPropagation();
            ev.preventDefault();
            this.do_action({
                name: _t("Inbox"),
                type: 'ir.actions.act_window',
                res_model: 'help.ticket',
                view_mode: 'tree,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [['stage_id.name', 'in', ['Inbox', 'Draft']]],
                context: {default_stage_id_name: 'Draft'},
                target: 'current'
            });
        },
        // Event handler for clicking the in-progress tickets
        tickets_inprogress: function (ev) {
            var self = this;
            ev.stopPropagation();
            ev.preventDefault();
            this.do_action({
                name: _t("In Progress"),
                type: 'ir.actions.act_window',
                res_model: 'help.ticket',
                view_mode: 'tree,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [['stage_id.name', '=', 'In Progress']],
                context: {create: false},
                target: 'current'
            });
        },
        // Event handler for clicking the done tickets
        tickets_done: function (ev) {
            var self = this;
            ev.stopPropagation();
            ev.preventDefault();
            this.do_action({
                name: _t("Done"),
                type: 'ir.actions.act_window',
                res_model: 'help.ticket',
                view_mode: 'tree,form',
                views: [[false, 'list'], [false, 'form']],
                domain: [['stage_id.name', '=', 'Done']],
                context: {create: false},
                target: 'current'
            });
        },
        // Event handler for clicking the helpdesk teams
        helpdesk_teams: function (ev) {
            var self = this;
            ev.stopPropagation();
            ev.preventDefault();
            this.do_action({
                name: _t("Teams"),
                type: 'ir.actions.act_window',
                res_model: 'help.team',
                view_mode: 'tree,form',
                views: [[false, 'list'], [false, 'form']],
                target: 'current'
            });
        },
    });
    // Register the Dashboard class in the action registry
    core.action_registry.add("helpdesk_dashboard", DashBoard);
    return DashBoard;
});