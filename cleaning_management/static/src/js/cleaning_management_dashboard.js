odoo.define('cleaning_management.dashboard_action', function(require) {
    "use strict";
    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var QWeb = core.qweb;
    var rpc = require('web.rpc');
    var CustomDashBoard = AbstractAction.extend({
        /**
         *  Obtain yearly, monthly, quarterly, and weekly bookings,
         as well as clean and dirt reports.
         */
        template: 'CleaningDashBoard',
        events: {
            'click .cleaning_cooking': 'get_bookings',
            'click .cleaning_teams': 'get_teams',
            'click .cleaning_count': 'get_cleaning',
            'click .dirty_count': 'get_dirty',
            'change #filtration': function(e) {
                e.stopPropagation();
                // Return elements where event occurred
                var target = this.$(e.target);
                if (target.val() == "this_year") {
                    this.onclick_this_year(target.val());
                } else if (target.val() == "this_quarter") {
                    this.onclick_this_quarter(target.val());
                } else if (target.val() == "this_month") {
                    this.onclick_this_month(target.val());
                } else if (target.val() == "this_week") {
                    this.onclick_this_week(target.val());
                }
            },
        },
        init: function(parent, context) {
            this._super(parent, context);
            this.dashboards_templates = ['CleaningDashboardProject',
                'DashboardProject', 'CleaningProject'
            ];
            this.today_sale = [];
        },
        //   Begin the function with the monthly records of bookings and inspections.
        start: function() {
            var self = this;
            this.set("title", 'Dashboard');
            return this._super().then(function() {
                self.render_dashboards();
                self.render_graphs();
                self.$("#activity_week").hide();
                self.$("#activity_year").hide();
                self.$("#activity_quarter").hide();
                self.$("#activity_month").show();
                self.$("#quality_week").hide();
                self.$("#quality_month").show();
                self.$("#quality_quarter").hide();
                self.$("#quality_year").hide();
                rpc.query({
                        model: "cleaning.management.dashboard",
                        method: "cleaning_count",
                        args: [0],
                    })
                    .then(function(result) {
                        if ((result['inspections'].length > 0) &&
                            (result['bookings'].length > 0)) {
                            self.$(".report").show();
                            self.$(".bookings").show();
                            self.$(".quality").show();
                        } else if (result['bookings'].length > 0) {
                            self.$(".report").show();
                            self.$(".bookings").show();
                            self.$(".quality").hide();
                        } else if (result['inspections'].length > 0) {
                            self.$(".report").show();
                            self.$(".bookings").hide();
                            self.$(".quality").show();
                        } else {
                            self.$(".report").hide();
                            self.$(".bookings").hide();
                            self.$(".quality").hide();
                        }
                    })
            });
        },
        //Generate a dashboard displaying the count of bookings, dirty instances, completed cleanings, and the cleaning team.
        render_dashboards: function() {
            var self = this;
            _.each(this.dashboards_templates, function(template) {
                self.$('.o_pj_dashboard').append(QWeb.render(template, {
                    widget: self
                }));
            });
            rpc.query({
                    model: "cleaning.management.dashboard",
                    method: "get_dashboard_count",
                    args: [0],
                })
                .then(function(result) {
                    self.$("#bookings_count").append("<span class='stat-digit'>" + result.bookings +
                        "</span>");
                    self.$("#teams_count").append("<span class='stat-digit'>" + result.teams +
                        "</span>");
                    self.$("#cleaning_count").append("<span class='stat-digit'>" + result.cleaned +
                        "</span>");
                    self.$("#dirty_count").append("<span class='stat-digit'>" + result.dirty +
                        "</span>");
                });
        },
        on_reverse_breadcrumb: function() {
            var self = this;
            self.$('.o_pj_dashboard').empty();
            self.render_dashboards();
        },
        // Get booking records
        get_bookings: function() {
            this.do_action({
                name: ("Bookings"),
                type: 'ir.actions.act_window',
                res_model: 'cleaning.booking',
                view_mode: 'tree,form,calendar',
                views: [
                    [false, 'list'],
                    [false, 'form']
                ],
                domain: [
                    ['state', '=', 'booked']
                ],
                target: 'current',
            })
        },
        // Get team count records
        get_teams: function() {
            this.do_action({
                name: ("Teams"),
                type: 'ir.actions.act_window',
                res_model: 'cleaning.team',
                view_mode: 'tree,form,calendar',
                views: [
                    [false, 'list'],
                    [false, 'form']
                ],
                target: 'current',
            })
        },
        // Get cleaning count
        get_cleaning: function() {
            this.do_action({
                name: ("Count of Cleaning"),
                type: 'ir.actions.act_window',
                res_model: 'cleaning.inspection',
                view_mode: 'tree,form,calendar',
                views: [
                    [false, 'list'],
                    [false, 'form']
                ],
                domain: [
                    ['state', '=', 'cleaned']
                ],
                target: 'current',
            })
        },
        // Get dirty count
        get_dirty: function() {
            this.do_action({
                name: ("Count of dirty"),
                type: 'ir.actions.act_window',
                res_model: 'cleaning.inspection',
                view_mode: 'tree,form,calendar',
                views: [
                    [false, 'list'],
                    [false, 'form']
                ],
                domain: [
                    ['state', '=', 'dirty']
                ],
                target: 'current',
            })
        },
        render_graphs: function() {
            var self = this;
            self.render_the_graph();
        },
        //Generate a graph representing the yearly, monthly, weekly, and quarterly records.
        render_the_graph: function() {
            var self = this
            var ctx = self.$(".total_bookings_year");
            rpc.query({
                model: "cleaning.management.dashboard",
                method: "get_the_booking_year",
                args: [0],
            }).then(function(result) {
                self.total_booking_stage =
                    result['total_booking_stage_year'],
                    self.total_booking_stage_draft_year =
                    result['total_booking_stage_draft_year'],
                    self.total_booking_stage_booked_year =
                    result['total_booking_stage_booked_year'],
                    self.total_booking_stage_cleaned_year =
                    result['total_booking_stage_cleaned_year'],
                    self.total_booking_stage_canceled_year =
                    result['total_booking_stage_canceled_year']
                const ctx = self.$('#activity_year')
                new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: result['total_booking_stage_year'],
                        datasets: [{
                            label: 'Stage',
                            data: [
                    result['total_booking_stage_draft_year'],
                    result['total_booking_stage_booked_year'],
                    result['total_booking_stage_cleaned_year'],
                    result['total_booking_stage_canceled_year']
                ],
                            borderWidth: 1
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        }
                    }
                });
            });
            var self = this
            var ctx = self.$(".total_bookings_week");
            rpc.query({
                model: "cleaning.management.dashboard",
                method: "get_the_booking_week",
                args: [0],
            }).then(function(result) {
                self.total_booking_stage =
                    result['total_booking_stage_week'],
                    self.total_booking_stage_draft =
                    result['total_booking_stage_draft_week'],
                    self.total_booking_stage_booked =
                    result['total_booking_stage_booked_week'],
                    self.total_booking_stage_cleaned =
                    result['total_booking_stage_cleaned_week'],
                    self.total_booking_stage_canceled =
                    result['total_booking_stage_canceled_week']
                const ctx = self.$('#activity_week')
                new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: result['total_booking_stage_week'],
                        datasets: [{
                            label: 'Stage',
                            data: [
                    result['total_booking_stage_draft_week'],
                    result['total_booking_stage_booked_week'],
                    result['total_booking_stage_cleaned_week'],
                    result['total_booking_stage_canceled_week']
                ],
                            borderWidth: 1
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        }
                    }
                });
            });
            var self = this
            var ctx = self.$(".total_bookings_month");
            rpc.query({
                model: "cleaning.management.dashboard",
                method: "get_the_booking_month",
                args: [0],
            }).then(function(result) {
                const dataPoints = [
                    result['total_booking_stage_draft_month'],
                    result['total_booking_stage_booked_month'],
                    result['total_booking_stage_cleaned_month'],
                    result['total_booking_stage_canceled_month']
                ].filter(value => value !== null && value !== '' &&
                    value !== 0);
                const ctx = self.$('#activity_month')
                new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: result['total_booking_stage_month'],
                        datasets: [{
                            label: 'Stage',
                            data: dataPoints,
                            borderWidth: 1
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        }
                    }
                });
            });
            var self = this
            var ctx = self.$(".total_bookings_quarter");
            rpc.query({
                model: "cleaning.management.dashboard",
                method: "get_the_booking_quarter",
                args: [0],
            }).then(function(result) {
                self.total_booking_stage =
                    result['total_booking_stage_quarter'],
                    self.total_booking_stage_draft =
                    result['total_booking_stage_draft_quarter'],
                    self.total_booking_stage_booked =
                    result['total_booking_stage_booked_quarter'],
                    self.total_booking_stage_cleaned =
                    result['total_booking_stage_cleaned_quarter'],
                    self.total_booking_stage_canceled =
                    result['total_booking_stage_canceled_quarter']
                const ctx = self.$('#activity_quarter')
                new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: result['total_booking_stage_quarter'],
                        datasets: [{
                            label: 'Stage',
                            data: [
                    result['total_booking_stage_draft_quarter'],
                    result['total_booking_stage_booked_quarter'],
                    result['total_booking_stage_cleaned_quarter'],
                    result['total_booking_stage_canceled_quarter']
                ],
                            borderWidth: 1
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        }
                    }
                });
            });
            var self = this
            var ctx = self.$(".total_quality_year");
            rpc.query({
                model: "cleaning.management.dashboard",
                method: "quality_year",
                args: [0],
            }).then(function(result) {
                self.quality_year = result['quality_year'],
                    self.cleaned_quality_year = result['cleaned_quality_year'],
                    self.dirty_quality_year = result['dirty_quality_year']
                const ctx = self.$('#quality_year')
                new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: result['quality_year'],
                        datasets: [{
                            label: 'Stage',
                            data: [result['cleaned_quality_year'],
                                result['dirty_quality_year']
                            ],
                            borderWidth: 1
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        }
                    }
                });
            });
            var self = this
            var ctx = self.$(".total_quality_week");
            rpc.query({
                model: "cleaning.management.dashboard",
                method: "quality_week",
                args: [0],
            }).then(function(result) {
                self.quality_week = result['quality_week'],
                    self.cleaned_quality_week = result['cleaned_quality_week'],
                    self.dirty_quality_week = result['dirty_quality_week']
                const ctx = self.$('#quality_week')
                new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: result['quality_week'],
                        datasets: [{
                            label: 'Stage',
                            data: [result['cleaned_quality_week'],
                                result['dirty_quality_week']
                            ],
                            borderWidth: 1
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        }
                    }
                });
            });
            var self = this
            var ctx = self.$(".total_quality_month");
            rpc.query({
                model: "cleaning.management.dashboard",
                method: "quality_month",
                args: [0],
            }).then(function(result) {
                self.quality_month = result['quality_month'],
                    self.cleaned_quality_month = result['cleaned_quality_month'],
                    self.dirty_quality_month = result['dirty_quality_month']
                const ctx = self.$('#quality_month')
                new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: result['quality_month'],
                        datasets: [{
                            label: 'Stage',
                            data: [result['cleaned_quality_month'],
                                result['dirty_quality_month']
                            ],
                            borderWidth: 1
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        }
                    }
                });
            });
            var self = this
            var ctx = self.$(".total_quality_quarter");
            rpc.query({
                model: "cleaning.management.dashboard",
                method: "quality_quarter",
                args: [0],
            }).then(function(result) {
                self.quality_quarter = result['quality_quarter'],
                    self.cleaned_quality_year = result['cleaned_quality_quarter'],
                    self.dirty_quality_year = result['dirty_quality_quarter']
                const ctx = self.$('#quality_quarter')
                new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: result['quality_quarter'],
                        datasets: [{
                            label: 'Stage',
                            data: [result['cleaned_quality_quarter'],
                                result['dirty_quality_quarter']
                            ],
                            borderWidth: 1
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        }
                    }
                });
            });
        },
        //  Show yearly result
        onclick_this_year: function(ev) {
            self.$("#activity_week").hide();
            self.$("#activity_month").hide();
            self.$("#activity_quarter").hide();
            self.$("#activity_year").show();
            self.$("#quality_week").hide();
            self.$("#quality_month").hide();
            self.$("#quality_quarter").hide();
            self.$("#quality_year").show();
        },
        //    Show monthly result
        onclick_this_month: function(ev) {
            self.$("#activity_week").hide();
            self.$("#activity_year").hide();
            self.$("#activity_quarter").hide();
            self.$("#activity_month").show();
            self.$("#quality_week").hide();
            self.$("#quality_month").show();
            self.$("#quality_quarter").hide();
            self.$("#quality_year").hide();
        },
        //    Show weekly result
        onclick_this_week: function(ev) {
            self.$("#activity_year").hide();
            self.$("#activity_month").hide();
            self.$("#activity_quarter").hide();
            self.$("#activity_week").show();
            self.$("#quality_week").show();
            self.$("#quality_month").hide();
            self.$("#quality_quarter").hide();
            self.$("#quality_year").hide();
        },
        //    Show quarterly result
        onclick_this_quarter: function(ev) {
            self.$("#activity_week").hide();
            self.$("#activity_month").hide();
            self.$("#activity_year").hide();
            self.$("#activity_quarter").show();
            self.$("#quality_week").hide();
            self.$("#quality_month").hide();
            self.$("#quality_quarter").show();
            self.$("#quality_year").hide();
        },
    })
    core.action_registry.add('cleaning_dashboard_tags', CustomDashBoard);
    return CustomDashBoard;
})
