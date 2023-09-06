odoo.define("odoo_website_helpdesk_dashboard.dashboard_view", function (require) {
    "use strict";

    const AbstractAction = require("web.AbstractAction");
    const core = require("web.core");
    const rpc = require("web.rpc");
    var ajax = require("web.ajax");
    const _t = core._t;
    const QWeb = core.qweb;
    const DashBoard = AbstractAction.extend({
        template: "HelpDesk_Dashboard",
        events: {
            "click .inbox_tickets": "tickets_inbox",
            "click .inprogress_tickets": "tickets_inprogress",
            "click .done_tickets": "tickets_done",
            "click .team_card": "helpdesk_teams"
        },
        init: function (parent, context) {
            this._super(parent, context);
            this.dashboards_templates = ['DashBoardHelpDesk'];

        },
        start: function () {
            var self = this;
            this.set("title", 'Dashboard');
            return this._super().then(function () {
                self.render_dashboards();
                self.render_graphs();
                self.$el.parent().addClass('oe_background_grey');
            });

        },
        render_graphs: function () {
            var self = this;
            self.render_tickets_month_graph();
            self.render_team_ticket_count_graph();
//            self.render_projects_ticket_graph();
//            self.render_billed_task_team_graph();
//            self.render_team_ticket_done_graph();

        },
      render_tickets_month_graph: function () {
    var self = this;
    var ctx = self.$(".ticket_month");
    rpc.query({
        model: "help.ticket",
        method: "get_tickets_view",
    }).then(function (values) {
        var data = {
            labels: ['New', 'In Progress', 'Solved'],
            datasets: [{
                data: [values.inbox_count, values.progress_count, values.done_count],
                backgroundColor: [
                    "#665191",
                    "#ff7c43",
                    "#ffa600"
                ],
                borderColor: [
                    "#003f5c",
                    "#2f4b7c",
                    "#f95d6a"
                ],
                borderWidth: 1
            }]
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

        //create Chart class object
        var chart = new Chart(ctx, {
            type: "doughnut",
            data: data,
            options: options
        });
    });
},

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

                //options
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

                //create Chart class object
                var chart = new Chart(ctx, {
                    type: "bar",
                    data: data,
                    options: options
                });
            });
        },


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
            })
                .then(function (result) {
                    $("#inbox_count").append("<span class='stat-digit'>" + result.inbox_count + "</span>");
                    $("#inprogress_count").append("<span class='stat-digit'>" + result.progress_count + "</span>");
                    $("#done_count").append("<span class='stat-digit'>" + result.done_count + "</span>");
                    $("#team_count").append("<span class='stat-digit'>" + result.team_count + "</span>");


                        var priorityCounts = {
                        very_low: result.very_low_count1,
                        low: result.low_count1,
                        normal: result.normal_count1,
                        high: result.high_count1,
                        very_high : result.very_high_count1
                        // Add other priorities and their corresponding count properties
                    };

                    // Loop through the priorities and create progress bars
                    for (var priority in priorityCounts) {
                        var progressBarWidth = priorityCounts[priority] + "%";

                        var progressBar = $("<div class='progress-bar'></div>").css("width", progressBarWidth);
                        var progressBarContainer = $("<div class='progress'></div>").append(progressBar);
                        var progressValue = $("<div class='progress-value'></div>").text(priorityCounts[priority] + "%");

                        // Append the progress bar container to elements with class corresponding to the priority
                        $("." + priority + "_count").append(progressBarContainer);
                        $("." + priority + "_count .progress-value").append(progressValue);

                    }

                         var tbody = $(".ticket-details");
                        var ticket_details = result.ticket_details;

                        for (var i = 0; i < ticket_details.length; i++) {
                            var ticket = ticket_details[i]; // Get the current ticket object
                            var row = $("<tr></tr>");
                            // Assuming you have the Base64-encoded image data in a variable called ticket.assigned_image
                           var base64Image = ticket.assigned_image;

                             var assignedUserCell = $("<td class='td'></td>");
                            var imgElement = $("<img>");
                            imgElement.attr("src", "data:image/png;base64," + base64Image); // Set the image source
                            imgElement.attr("alt", "User Image"); // Set an alt attribute for accessibility
                            imgElement.addClass("user-image"); // Add the 'oe-avatar' class to the <img> element

                            // Append the img element to the assignedUserCell
                            assignedUserCell.append(imgElement);

                            // Append the assignedUserCell to the row
                            row.append(assignedUserCell);


                            row.append("<td class='td'>" + ticket.customer_name + "</td>");
                            row.append("<td class='td'>" + ticket.ticket_name + "</td>");
                            row.append(assignedUserCell);
                            row.append("<td>" + ticket.assigned_to + "</td>");
                            row.append("<td>" + ticket.subject + "</td>");
                            row.append("<td>" + ticket.priority + "</td>");
                            tbody.append(row);
                        }





                    $(".response").append(result.response);
                    ajax.jsonRpc("/help/tickets", "call", {}).then(function (values) {
                        $('.pending_tickets').append(values);
                    });

                });
        },

        //events
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

    core.action_registry.add("helpdesk_dashboard", DashBoard);
    return DashBoard;
});
