odoo.define('crm_dashboard.CRMDashboard', function (require) {
    'use strict';
    var AbstractAction = require('web.AbstractAction');
    var ajax = require('web.ajax');
    var core = require('web.core');
    var rpc = require('web.rpc');
    var web_client = require('web.web_client');
    var session = require('web.session');
    var _t = core._t;
    var QWeb = core.qweb;
    var self = this;
    var currency;
    var DashBoard = AbstractAction.extend({
        contentTemplate: 'CRMdashboard',
        events: {
            'click .my_lead': 'my_lead',
            'click .opportunity': 'opportunity',
            'click .unassigned_leads': 'unassigned_leads',
            'click .exp_revenue': 'exp_revenue',
            'click .revenue_card': 'revenue_card',
            'change #income_expense_values': function(e) {
                e.stopPropagation();
                var $target = $(e.target);
                var value = $target.val();
                if (value=="this_year"){
                    this.onclick_this_year($target.val());
                }else if (value=="this_quarter"){
                    this.onclick_this_quarter($target.val());
                }else if (value=="this_month"){
                    this.onclick_this_month($target.val());
                }else if (value=="this_week"){
                    this.onclick_this_week($target.val());
                }
            },
            'change #total_loosed_crm': function(e) {
                e.stopPropagation();
                var $target = $(e.target);
                var value = $target.val();
                if (value=="lost_last_12months"){
                    this.onclick_lost_last_12months($target.val());
                }else if (value=="lost_last_6months"){
                    this.onclick_lost_last_6months($target.val());
                }else if (value=="lost_last_month"){
                    this.onclick_lost_last_month($target.val());
                }
            },
            'change #total_loosed_crm_sub': function(e) {
                e.stopPropagation();
                var $target = $(e.target);
                var value = $target.val();
                if (value=="sub_lost_last_12months"){
                    this.onclick_sub_lost_last_12months($target.val());
                }else if (value=="sub_lost_last_6months"){
                    this.onclick_sub_lost_last_6months($target.val());
                }else if (value=="sub_lost_last_month"){
                    this.onclick_sub_lost_last_month($target.val());
                }
            },
        },

        init: function(parent, context) {
            this._super(parent, context);
            this.upcoming_events = [];
            this.dashboards_templates = ['LoginUser','Managercrm','Admincrm', 'SubDashboard'];
            this.login_employee = [];
        },

        willStart: function(){
            var self = this;
            this.login_employee = {};
            return this._super()
            .then(function() {

                var def0 =  self._rpc({
                    model: 'crm.lead',
                    method: 'check_user_group'
                }).then(function(result) {
                    if (result == true){
                        self.is_manager = true;
                    }
                    else{
                        self.is_manager = false;
                    }
                });

                var def1 = self._rpc({
                    model: "crm.lead",
                    method: "get_upcoming_events",
                })
                .then(function (res) {
                    self.upcoming_events = res['event'];
                });

                var def2 = self._rpc({
                    model: "crm.lead",
                    method: "get_top_deals",
                })
                .then(function (res) {
                    self.top_deals = res['deals'];
                });

                var def3 = self._rpc({
                    model: "crm.lead",
                    method: "get_monthly_goal",
                })
                .then(function (res) {
                    self.monthly_goals = res['goals'];
                });

                var def4 = self._rpc({
                    model: "crm.lead",
                    method: "get_top_sp_revenue",
                })
                .then(function (res) {
                    self.top_sp_revenue = res['top_revenue'];
                });

                var def5 = self._rpc({
                    model: "crm.lead",
                    method: "get_country_revenue",
                })
                .then(function (res) {
                    self.top_country_revenue = res['country_revenue'];
                });

                var def6 = self._rpc({
                    model: "crm.lead",
                    method: "get_country_count",
                })
                .then(function (res) {
                    self.top_country_count = res['country_count'];
                });

                var def7 = self._rpc({
                    model: "crm.lead",
                    method: "get_lost_reason_count",
                })
                .then(function (res) {
                    self.top_reason_count = res['reason_count'];
                });

                var def8 = self._rpc({
                    model: "crm.lead",
                    method: "get_ratio_based_country",
                })
                .then(function (res) {
                    self.top_country_wise_ratio = res['country_wise_ratio'];
                });

                var def9 = self._rpc({
                    model: "crm.lead",
                    method: "get_ratio_based_sp",
                })
                .then(function (res) {
                    self.top_salesperson_wise_ratio = res['salesperson_wise_ratio'];
                });

                var def10 = self._rpc({
                    model: "crm.lead",
                    method: "get_ratio_based_sales_team",
                })
                .then(function (res) {
                    self.top_sales_team_wise_ratio = res['sales_team_wise_ratio'];
                });

                var def11 = self._rpc({
                    model: "crm.lead",
                    method: "get_recent_activities",
                })
                .then(function (res) {
                    self.recent_activities = res['activities'];
                });

                var def12 = self._rpc({
                    model: "crm.lead",
                    method: "get_count_unassigned",
                })
                .then(function (res) {
                    self.get_count_unassigned = res['count_unassigned'];
                });

                var def13 = self._rpc({
                    model: "crm.lead",
                    method: "get_top_sp_by_invoice",
                })
                .then(function (res) {
                    self.top_sp_by_invoice = res['sales_person_invoice'];
                });

                return $.when(def0, def1, def2, def3, def4, def5, def6, def7, def8, def9, def10, def11, def12, def13);
            });
        },

        onclick_this_year: function (ev) {
            var self = this;
            rpc.query({
                model: 'crm.lead',
                method: 'crm_year',
                args: [],
            })
            .then(function (result) {
                $('#leads_this_quarter').hide();
                $('#opp_this_quarter').hide();
                $('#exp_rev_this_quarter').hide();
                $('#rev_this_quarter').hide();
                $('#ratio_this_quarter').hide();
                $('#avg_time_this_quarter').hide();
                $('#total_revenue_this_quarter').hide();
                $('#leads_this_month').hide();
                $('#opp_this_month').hide();
                $('#exp_rev_this_month').hide();
                $('#rev_this_month').hide();
                $('#ratio_this_month').hide();
                $('#avg_time_this_month').hide();
                $('#total_revenue_this_month').hide();
                $('#leads_this_week').hide();
                $('#opp_this_week').hide();
                $('#exp_rev_this_week').hide();
                $('#rev_this_week').hide();
                $('#ratio_this_week').hide();
                $('#avg_time_this_week').hide();
                $('#total_revenue_this_week').hide();

                $('#leads_this_year').show();
                $('#opp_this_year').show();
                $('#exp_rev_this_year').show();
                $('#rev_this_year').show();
                $('#ratio_this_year').show();
                $('#avg_time_this_year').show();
                $('#total_revenue_this_year').show();

                $('#leads_this_year').empty();
                $('#opp_this_year').empty();
                $('#exp_rev_this_year').empty();
                $('#rev_this_year').empty();
                $('#ratio_this_year').empty();
                $('#avg_time_this_year').empty();
                $('#total_revenue_this_year').empty();

                $('#leads_this_year').append('<span>' + result.record + '</span>');
                $('#opp_this_year').append('<span>' + result.record_op + '</span>');
                $('#exp_rev_this_year').append('<span>' + self.monthly_goals[2] + '&nbsp' + result.record_rev_exp + '</span>');
                $('#rev_this_year').append('<span>' + self.monthly_goals[2] + '&nbsp' + result.record_rev + '</span>');
                $('#ratio_this_year').append('<span>' + result.record_ratio + '</span>');
                $('#avg_time_this_year').append('<span>' + result.avg_time + '&nbspsec' + '</span>');
                $('#total_revenue_this_year').append('<span>' + result.opportunity_ratio_value + '</span>');
            })
        },

        onclick_this_quarter: function (ev) {
            var self = this;
            rpc.query({
                model: 'crm.lead',
                method: 'crm_quarter',
                args: [],
            })
            .then(function (result) {
                $('#leads_this_year').hide();
                $('#opp_this_year').hide();
                $('#exp_rev_this_year').hide();
                $('#rev_this_year').hide();
                $('#ratio_this_year').hide();
                $('#avg_time_this_year').hide();
                $('#total_revenue_this_year').hide();
                $('#leads_this_month').hide();
                $('#opp_this_month').hide();
                $('#exp_rev_this_month').hide();
                $('#rev_this_month').hide();
                $('#ratio_this_month').hide();
                $('#avg_time_this_month').hide();
                $('#total_revenue_this_month').hide();
                $('#leads_this_week').hide();
                $('#opp_this_week').hide();
                $('#exp_rev_this_week').hide();
                $('#rev_this_week').hide();
                $('#ratio_this_week').hide();
                $('#avg_time_this_week').hide();
                $('#total_revenue_this_week').hide();

                $('#leads_this_quarter').show();
                $('#opp_this_quarter').show();
                $('#exp_rev_this_quarter').show();
                $('#rev_this_quarter').show();
                $('#ratio_this_quarter').show();
                $('#avg_time_this_quarter').show();
                $('#total_revenue_this_quarter').show();

                $('#leads_this_quarter').empty();
                $('#opp_this_quarter').empty();
                $('#exp_rev_this_quarter').empty();
                $('#rev_this_quarter').empty();
                $('#ratio_this_quarter').empty();
                $('#avg_time_this_quarter').empty();
                $('#total_revenue_this_quarter').empty();

                $('#leads_this_quarter').append('<span>' + result.record + '</span>');
                $('#opp_this_quarter').append('<span>' + result.record_op + '</span>');
                $('#exp_rev_this_quarter').append('<span>' + self.monthly_goals[2] + '&nbsp' + result.record_rev_exp + '</span>');
                $('#rev_this_quarter').append('<span>' + self.monthly_goals[2] + '&nbsp' + result.record_rev + '</span>');
                $('#ratio_this_quarter').append('<span>' + result.record_ratio + '</span>');
                $('#avg_time_this_quarter').append('<span>' + result.avg_time  + '&nbspsec' + '</span>');
                $('#total_revenue_this_quarter').append('<span>' + result.opportunity_ratio_value + '</span>');
            })
        },

        onclick_this_month: function (ev) {
            var self = this;
            rpc.query({
                model: 'crm.lead',
                method: 'crm_month',
                args: [],
            })
            .then(function (result) {
                $('#leads_this_year').hide();
                $('#opp_this_year').hide();
                $('#exp_rev_this_year').hide();
                $('#rev_this_year').hide();
                $('#ratio_this_year').hide();
                $('#avg_time_this_year').hide();
                $('#total_revenue_this_year').hide();
                $('#leads_this_quarter').hide();
                $('#opp_this_quarter').hide();
                $('#exp_rev_this_quarter').hide();
                $('#rev_this_quarter').hide();
                $('#ratio_this_quarter').hide();
                $('#avg_time_this_quarter').hide();
                $('#total_revenue_this_quarter').hide();
                $('#leads_this_week').hide();
                $('#opp_this_week').hide();
                $('#exp_rev_this_week').hide();
                $('#rev_this_week').hide();
                $('#ratio_this_week').hide();
                $('#avg_time_this_week').hide();
                $('#total_revenue_this_week').hide();

                $('#leads_this_month').show();
                $('#opp_this_month').show();
                $('#exp_rev_this_month').show();
                $('#rev_this_month').show();
                $('#ratio_this_month').show();
                $('#avg_time_this_month').show();
                $('#total_revenue_this_month').show();

                $('#leads_this_month').empty();
                $('#opp_this_month').empty();
                $('#exp_rev_this_month').empty();
                $('#rev_this_month').empty();
                $('#ratio_this_month').empty();
                $('#avg_time_this_month').empty();
                $('#total_revenue_this_month').empty();

                $('#leads_this_month').append('<span>' + result.record + '</span>');
                $('#opp_this_month').append('<span>' + result.record_op + '</span>');
                $('#exp_rev_this_month').append('<span>' + self.monthly_goals[2] + '&nbsp' + result.record_rev_exp + '</span>');
                $('#rev_this_month').append('<span>' + self.monthly_goals[2] + '&nbsp' + result.record_rev + '</span>');
                $('#ratio_this_month').append('<span>' + result.record_ratio + '</span>');
                $('#avg_time_this_month').append('<span>' + result.avg_time  + '&nbspsec' + '</span>');
                $('#total_revenue_this_month').append('<span>' + result.opportunity_ratio_value + '</span>');
            })
        },

        onclick_this_week: function (ev) {
            var self = this;
            rpc.query({
                model: 'crm.lead',
                method: 'crm_week',
                args: [],
            })
            .then(function (result) {
                $('#leads_this_year').hide();
                $('#opp_this_year').hide();
                $('#exp_rev_this_year').hide();
                $('#rev_this_year').hide();
                $('#ratio_this_year').hide();
                $('#avg_time_this_year').hide();
                $('#total_revenue_this_year').hide();
                $('#leads_this_quarter').hide();
                $('#opp_this_quarter').hide();
                $('#exp_rev_this_quarter').hide();
                $('#rev_this_quarter').hide();
                $('#ratio_this_quarter').hide();
                $('#avg_time_this_quarter').hide();
                $('#total_revenue_this_quarter').hide();
                $('#leads_this_month').hide();
                $('#opp_this_month').hide();
                $('#exp_rev_this_month').hide();
                $('#rev_this_month').hide();
                $('#ratio_this_month').hide();
                $('#avg_time_this_month').hide();
                $('#total_revenue_this_month').hide();

                $('#leads_this_week').show();
                $('#opp_this_week').show();
                $('#exp_rev_this_week').show();
                $('#rev_this_week').show();
                $('#ratio_this_week').show();
                $('#avg_time_this_week').show();
                $('#total_revenue_this_week').show();

                $('#leads_this_week').empty();
                $('#opp_this_week').empty();
                $('#exp_rev_this_week').empty();
                $('#rev_this_week').empty();
                $('#ratio_this_week').empty();
                $('#avg_time_this_week').empty();
                $('#total_revenue_this_week').empty();

                $('#leads_this_week').append('<span>' + result.record + '</span>');
                $('#opp_this_week').append('<span>' + result.record_op + '</span>');
                $('#exp_rev_this_week').append('<span>' + self.monthly_goals[2] + '&nbsp' + result.record_rev_exp + '</span>');
                $('#rev_this_week').append('<span>' + self.monthly_goals[2] + '&nbsp' + result.record_rev + '</span>');
                $('#ratio_this_week').append('<span>' + result.record_ratio + '</span>');
                $('#avg_time_this_week').append('<span>' + result.avg_time + '&nbspsec' + '</span>');
                $('#total_revenue_this_week').append('<span>' + result.opportunity_ratio_value + '</span>');
            })
        },

        renderElement: function (ev) {
            var self = this;
            $.when(this._super())
            .then(function (ev) {
                rpc.query({
                    model: "crm.lead",
                    method: "lead_details_user",
                    args: [],
                })
                .then(function (result) {
                    $('#leads_this_month').append('<span>' + result.record + '</span>');
                    $('#opp_this_month').append('<span>' + result.record_op + '</span>');
                    $('#exp_rev_this_month').append('<span>' + self.monthly_goals[2] + '&nbsp' + result.record_rev_exp + '</span>');
                    $('#rev_this_month').append('<span>' + self.monthly_goals[2] + '&nbsp' + result.record_rev + '</span>');
                    $('#ratio_this_month').append('<span>' + result.record_ratio + '</span>');
                    $('#avg_time_this_month').append('<span>' + result.avg_time  + '&nbspsec' + '</span>');
                    $('#total_revenue_this_month').append('<span>' + result.opportunity_ratio_value + '</span>');
                    $('#target').append('<span>' + result.target  +'</span>');
                    $('#ytd_target').append('<span>' + result.ytd_target  +'</span>');
                    $('#difference').append('<span>' + result.difference  +'</span>');
                    $('#won').append('<span>' + result.won  +'</span>');
                })
            });
        },

        //lead
        my_lead: function(e) {
            var self = this;
            e.stopPropagation();
            e.preventDefault();
            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };
            this.do_action({
                name: _t("My Leads"),
                type: 'ir.actions.act_window',
                res_model: 'crm.lead',
                view_mode: 'tree,form,calendar',
                views: [[false, 'list'],[false, 'form']],
                domain: [['user_id', '=', session.uid]],
                target: 'current',
            }, options)
        },

        //opportunity
        opportunity: function(e) {
            var self = this;
            e.stopPropagation();
            e.preventDefault();
            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };
            this.do_action({
                name: _t("Opportunity"),
                type: 'ir.actions.act_window',
                res_model: 'crm.lead',
                view_mode: 'tree,form,calendar',
                views: [[false, 'list'],[false, 'form']],
                domain: [['user_id', '=', session.uid], ['type','=', 'opportunity']],
                target: 'current',
            }, options)
        },

        //expected_revenue
        exp_revenue: function(e) {
            var self = this;
            e.stopPropagation();
            e.preventDefault();
            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };
            this.do_action({
                name: _t("Expected Revenue"),
                type: 'ir.actions.act_window',
                res_model: 'crm.lead',
                view_mode: 'tree,form,calendar',
                views: [[false, 'list'],[false, 'form']],
                domain: [['user_id','=', session.uid], ['type','=', 'opportunity'], ['active','=', true]],
                target: 'current',
            }, options)
        },

        //revenue
        revenue_card: function(e) {
            var self = this;
            e.stopPropagation();
            e.preventDefault();
            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };
            this.do_action({
                name: _t("Revenue"),
                type: 'ir.actions.act_window',
                res_model: 'crm.lead',
                view_mode: 'tree,form,calendar',
                views: [[false, 'list'],[false, 'form']],
                domain: [['user_id','=', session.uid], ['type','=', 'opportunity'], ['stage_id','=', 4]],
                target: 'current',
            }, options)
        },

        //unassigned_leads
        unassigned_leads: function(e) {
            var self = this;
            e.stopPropagation();
            e.preventDefault();
            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };
            this.do_action({
                name: _t("Unassigned Leads"),
                type: 'ir.actions.act_window',
                res_model: 'crm.lead',
                view_mode: 'tree,form,calendar',
                views: [[false, 'list'],[false, 'form']],
                domain: [['user_id','=', false],['type', '=', 'lead']],
                context: {'group_by': 'team_id'},
                target: 'current',
            }, options)
        },

        start: function() {
            var self = this;
            this.set("title", 'Dashboard');
            return this._super().then(function() {
                self.update_cp();
                self.render_dashboards();
                self.render_graphs();
                self.$el.parent().addClass('oe_background_grey');
            });
        },

        render_graphs: function(){
            var self = this;
            self.render_sales_activity_graph();
            self.render_leads_month_graph();
            self.funnel_chart();
            self.render_annual_chart_graph();
            self.render_campaign_leads_graph();
            self.render_medium_leads_graph();
            self.render_source_leads_graph();
            self.onclick_lost_last_12months();
            self.onclick_sub_lost_last_12months();
            self.render_lost_leads_graph();
            self.render_lost_leads_by_stage_graph();
            self.render_revenue_count_pie();
        },

        funnel_chart: function () {
            rpc.query({
                model: "crm.lead",
                method: "get_lead_stage_data",
            }).then(function (callbacks) {
                Highcharts.chart("container", {
                    chart: {
                        type: "funnel",
                    },
                    title: false,
                    credits: {
                        enabled: false
                    },
                    plotOptions: {
                        series: {
                            dataLabels: {
                                enabled: true,
                                softConnector: true
                            },
                            center: ['45%', '50%'],
                            neckWidth: '40%',
                            neckHeight: '35%',
                            width: '90%',
                            height: '80%'
                        }
                    },
                    series: [ {
                        name: "Number Of Leads",
                        data: callbacks,
                    }],
                });
            });
        },

        render_lost_leads_graph:function(){
            var self = this;
            var ctx = self.$(".lost_leads_graph");
            rpc.query({
                model: "crm.lead",
                method: "get_lost_lead_by_reason_pie",
            }).then(function (arrays) {
                var data = {
                    labels : arrays[1],
                    datasets: [{
                        label: "",
                        data: arrays[0],
                        backgroundColor: [
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

                //options
                var options = {
                    responsive: true,
                    title: false,
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

        render_lost_leads_by_stage_graph:function(){
            var self = this
            var ctx = self.$(".lost_leads_by_stage_graph");
            rpc.query({
                model: "crm.lead",
                method: "get_lost_lead_by_stage_pie",
            }).then(function (arrays) {
                var data = {
                    labels : arrays[1],
                    datasets: [{
                        label: "",
                        data: arrays[0],
                        backgroundColor: [
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

                //options
                var options = {
                    responsive: true,
                    title: false,
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

        render_sales_activity_graph:function(){
            var self = this
            var ctx = self.$(".sales_activity");
            rpc.query({
                model: "crm.lead",
                method: "get_the_sales_activity",
            }).then(function (arrays) {
                var data = {
                    labels : arrays[1],
                    datasets: [{
                        label: "",
                        data: arrays[0],
                        backgroundColor: [
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

        render_leads_month_graph:function(){
            var self = this
            var ctx = self.$(".lead_month");
            rpc.query({
                model: "crm.lead",
                method: "get_lead_month_pie",
            }).then(function (arrays) {
                var data = {
                    labels : arrays[1],
                    datasets: [{
                        label: "",
                        data: arrays[0],
                        backgroundColor: [
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

        render_revenue_count_pie:function(){
            var self = this;
            var ctx = self.$(".revenue_count_pie_canvas");
            rpc.query({
                model: "crm.lead",
                method: "revenue_count_pie",
            }).then(function (arrays) {
                var data = {
                    labels : arrays[1],
                    datasets: [{
                        label: "",
                        data: arrays[0],
                        backgroundColor: [
                            "#003f5c",
                            "#ff7c43",
                            "#f95d6a"
                        ],
                        borderColor: [
                            "#003f5c",
                            "#ff7c43",
                            "#f95d6a"
                        ],
                        borderWidth: 1
                    },]
                };

                //options
                var options = {
                    responsive: true,
                    title: false,
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

        render_annual_chart_graph:function(){
            var self = this
            var ctx = self.$(".annual_target");
            rpc.query({
                model: "crm.lead",
                method: "get_the_annual_target",
            }).then(function (arrays) {
                var data = {
                    labels : arrays[1],
                    datasets: [{
                        label: "",
                        data: arrays[0],
                        backgroundColor: [
                            "#003f5c",
                            "#f95d6a",
                            "#ff7c43",
                            "#6d5c16"
                        ],
                        borderColor: [
                            "#003f5c",
                            "#f95d6a",
                            "#ff7c43",
                            "#6d5c16"
                        ],
                        borderWidth: 1
                    },]
                };

                //options
                var options = {
                    responsive: true,
                    title: false,
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
                    type: "bar",
                    data: data,
                    options: {
                        responsive:true,
                        maintainAspectRatio: false,
                        legend: {
                            display: false //This will do the task
                        },
                    }
                });
            });
        },


        render_campaign_leads_graph:function(){
            var self = this
            var ctx = self.$(".campaign_source");
            rpc.query({
                model: "crm.lead",
                method: "get_the_campaign_pie",
            }).then(function (arrays) {
                var data = {
                    labels : arrays[1],
                    datasets: [{
                        label: "",
                        data: arrays[0],
                        backgroundColor: [
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

                //options
                var options = {
                    responsive: true,
                    title: false,
                    legend: {
                        display: true,
                        position: "bottom",
                        labels: {
                            fontColor: "#333",
                            fontSize: 14
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

        render_source_leads_graph:function(){
            var self = this
            var ctx = self.$(".source_lead");
            rpc.query({
                model: "crm.lead",
                method: "get_the_source_pie",
            }).then(function (arrays) {
                var data = {
                    labels : arrays[1],
                    datasets: [{
                        label: "",
                        data: arrays[0],
                        backgroundColor: [
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

                //options
                var options = {
                    responsive: true,
                    title: false,
                    legend: {
                        display: true,
                        position: "right",
                        labels: {
                            fontColor: "#333",
                            fontSize: 14
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

        render_medium_leads_graph:function(){
            var self = this
            var ctx = self.$(".medium_leads");
            rpc.query({
                model: "crm.lead",
                method: "get_the_medium_pie",
            }).then(function (arrays) {
                var data = {
                    labels : arrays[1],
                    datasets: [{
                        label: "",
                        data: arrays[0],
                        backgroundColor: [
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

                //options
                var options = {
                    responsive: true,
                    title: false,
                    legend: {
                        display: true,
                        position: "right",
                        labels: {
                            fontColor: "#333",
                            fontSize: 14
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

        onclick_lost_last_12months: function(ev) {
            var self = this;
            if( self.is_manager == true){
                self.initial_render = true;
                rpc.query({
                    model: "crm.lead",
                    method: "get_total_lost_crm",
                    args: ['12']
                }).then(function(result){
                    var ctx = document.getElementById("canvas").getContext('2d');
                    // Define the data
                    var lost_reason = result.month // Add data values to array
                    var count = result.count;
                    var myChart = new Chart(ctx, {
                        type: 'bar',
                        data: {
                            labels: lost_reason,//x axis
                            datasets: [{
                                label: 'Count', // Name the series
                                data: count, // Specify the data values array
                                backgroundColor: '#66aecf',
                                borderColor: '#66aecf',
                                barPercentage: 0.5,
                                barThickness: 6,
                                maxBarThickness: 8,
                                minBarLength: 0,
                                borderWidth: 1, // Specify bar border width
                                type: 'bar', // Set this data to a line chart
                                fill: false
                            }]
                        },
                        options: {
                            scales: {
                                y: {
                                    beginAtZero: true
                                },
                            },
                            responsive: true, // Instruct chart js to respond nicely.
                            maintainAspectRatio: false, // Add to prevent default behaviour of full-width/height
                        }
                    });
                });
            };
        },

        onclick_lost_last_6months: function(ev) {
            var self = this;
            self.initial_render = true;
            rpc.query({
                model: "crm.lead",
                method: "get_total_lost_crm",
                args: ['6']
            }).then(function(result){
                var ctx = document.getElementById("canvas").getContext('2d');
                // Define the data
                var lost_reason = result.month // Add data values to array
                var count = result.count;
                var myChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: lost_reason,//x axis
                        datasets: [{
                            label: 'Count', // Name the series
                            data: count, // Specify the data values array
                            backgroundColor: '#66aecf',
                            borderColor: '#66aecf',
                            barPercentage: 0.5,
                            barThickness: 6,
                            maxBarThickness: 8,
                            minBarLength: 0,
                            borderWidth: 1, // Specify bar border width
                            type: 'bar', // Set this data to a line chart
                            fill: false
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        },
                        responsive: true, // Instruct chart js to respond nicely.
                        maintainAspectRatio: false, // Add to prevent default behaviour of full-width/height
                    }
                });
            });
        },

        onclick_lost_last_month: function(ev) {
            var self = this;
            self.initial_render = true;
            rpc.query({
                model: "crm.lead",
                method: "get_total_lost_crm",
                args: ['1']
            }).then(function(result){
                var ctx = document.getElementById("canvas").getContext('2d');
                // Define the data
                var lost_reason = result.month // Add data values to array
                var count = result.count;
                var myChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: lost_reason,//x axis
                        datasets: [{
                            label: 'Count', // Name the series
                            data: count, // Specify the data values array
                            backgroundColor: '#66aecf',
                            borderColor: '#66aecf',
                            barPercentage: 0.5,
                            barThickness: 6,
                            maxBarThickness: 8,
                            minBarLength: 0,
                            borderWidth: 1, // Specify bar border width
                            type: 'bar', // Set this data to a line chart
                            fill: false
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        },
                        responsive: true, // Instruct chart js to respond nicely.
                        maintainAspectRatio: false, // Add to prevent default behaviour of full-width/height
                    }
                });
            });
        },

        onclick_sub_lost_last_12months: function(ev) {
            var self = this;
            if( self.is_manager == true){
                self.initial_render = true;
                rpc.query({
                    model: "crm.lead",
                    method: "get_total_lost_crm",
                    args: ['12']
                }).then(function(result){
                    var ctx = document.getElementById('canvas_graph').getContext('2d');
                    // Define the data
                    var lost_reason = result.month; // Add data values to array
                    var count = result.count;
                    var myChart = new Chart(ctx, {
                        type: 'bar',
                        data: {
                            labels: lost_reason,//x axis
                            datasets: [{
                                label: 'Count', // Name the series
                                data: count, // Specify the data values array
                                backgroundColor: '#66aecf',
                                borderColor: '#66aecf',
                                barPercentage: 0.5,
                                barThickness: 6,
                                maxBarThickness: 8,
                                minBarLength: 0,
                                borderWidth: 1, // Specify bar border width
                                type: 'bar', // Set this data to a line chart
                                fill: false
                            }]
                        },
                        options: {
                            scales: {
                                y: {
                                    beginAtZero: true
                                }
                            },
                            responsive: true, // Instruct chart js to respond nicely.
                            maintainAspectRatio: false, // Add to prevent default behaviour of full-width/height
                        }
                    });
                });
            };
        },

        onclick_sub_lost_last_6months: function(ev) {
            var self = this;
            self.initial_render = true;
            rpc.query({
                model: "crm.lead",
                method: "get_total_lost_crm",
                args: ['6']
            }).then(function(result){
                var ctx = document.getElementById("canvas_graph").getContext('2d');
                // Define the data
                var lost_reason = result.month // Add data values to array
                var count = result.count;
                var myChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: lost_reason,//x axis
                        datasets: [{
                            label: 'Count', // Name the series
                            data: count, // Specify the data values array
                            backgroundColor: '#66aecf',
                            borderColor: '#66aecf',
                            barPercentage: 0.5,
                            barThickness: 6,
                            maxBarThickness: 8,
                            minBarLength: 0,
                            borderWidth: 1, // Specify bar border width
                            type: 'bar', // Set this data to a line chart
                            fill: false
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        },
                        responsive: true, // Instruct chart js to respond nicely.
                        maintainAspectRatio: false, // Add to prevent default behaviour of full-width/height
                    }
                });
            });
        },

        onclick_sub_lost_last_month: function(ev) {
            var self = this;
            self.initial_render = true;
            rpc.query({
                model: "crm.lead",
                method: "get_total_lost_crm",
                args: ['1']
            }).then(function(result){
                var ctx = document.getElementById("canvas_graph").getContext('2d');
                // Define the data
                var lost_reason = result.month // Add data values to array
                var count = result.count;
                var myChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: lost_reason,//x axis
                        datasets: [{
                            label: 'Count', // Name the series
                            data: count, // Specify the data values array
                            backgroundColor: '#66aecf',
                            borderColor: '#66aecf',
                            barPercentage: 0.5,
                            barThickness: 6,
                            maxBarThickness: 8,
                            minBarLength: 0,
                            borderWidth: 1, // Specify bar border width
                            type: 'bar', // Set this data to a line chart
                            fill: false
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        },
                        responsive: true, // Instruct chart js to respond nicely.
                        maintainAspectRatio: false, // Add to prevent default behaviour of full-width/height
                    }
                });
            });
        },

        fetch_data: function() {
            var self = this;

            var def0 =  self._rpc({
                model: 'crm.lead',
                method: 'check_user_group'
            }).then(function(result) {
                if (result == true){
                    self.is_manager = true;
                }
                else{
                    self.is_manager = false;
                }
            });

            var def1 = self._rpc({
                model: "crm.lead",
                method: "get_upcoming_events",
            })
            .then(function (res) {
                self.upcoming_events = res['event'];
            });

            var def2 = self._rpc({
                model: "crm.lead",
                method: "get_top_deals",
            })
            .then(function (res) {
                self.top_deals = res['deals'];
            });

            var def3 = self._rpc({
                model: "crm.lead",
                method: "get_monthly_goal",
            })
            .then(function (res) {
                self.monthly_goals = res['goals'];
            });

            var def4 = self._rpc({
                model: "crm.lead",
                method: "get_top_sp_revenue",
            })
            .then(function (res) {
                self.top_sp_revenue = res['top_revenue'];
            });

            var def5 = self._rpc({
                model: "crm.lead",
                method: "get_country_revenue",
            })
            .then(function (res) {
                self.top_country_revenue = res['country_revenue'];
            });

            var def6 = self._rpc({
                model: "crm.lead",
                method: "get_country_count",
            })
            .then(function (res) {
                self.top_country_count = res['country_count'];
            });

            var def7 = self._rpc({
                model: "crm.lead",
                method: "get_lost_reason_count",
            })
            .then(function (res) {
                self.top_reason_count = res['reason_count'];
            });

            var def8 = self._rpc({
                model: "crm.lead",
                method: "get_ratio_based_country",
            })
            .then(function (res) {
                self.top_country_wise_ratio = res['country_wise_ratio'];
            });

            var def9 = self._rpc({
                model: "crm.lead",
                method: "get_ratio_based_sp",
            })
            .then(function (res) {
                self.top_salesperson_wise_ratio = res['salesperson_wise_ratio'];
            });

            var def10 = self._rpc({
                model: "crm.lead",
                method: "get_ratio_based_sales_team",
            })
            .then(function (res) {
                self.top_sales_team_wise_ratio = res['sales_team_wise_ratio'];
            });

            var def11 = self._rpc({
                model: "crm.lead",
                method: "get_recent_activities",
            })
            .then(function (res) {
                self.recent_activities = res['activities'];
            });

            var def12 = self._rpc({
                model: "crm.lead",
                method: "get_count_unassigned",
            })
            .then(function (res) {
                self.get_count_unassigned = res['count_unassigned'];
            });

            var def13 = self._rpc({
                model: "crm.lead",
                method: "get_top_sp_by_invoice",
            })
            .then(function (res) {
                self.top_sp_by_invoice = res['sales_person_invoice'];
            });

            return $.when(def0, def1, def2, def3, def4, def5, def6, def7, def8, def9, def10, def11, def12, def13);
        },

        render_dashboards: function() {
            var self = this;
            if (this.login_employee){
                var templates = []
                if( self.is_manager == true){
                    templates = ['LoginUser', 'Managercrm', 'Admincrm', 'SubDashboard'];
                }
                else{
                    templates = ['LoginUser','Managercrm'];
                }
                _.each(templates, function(template) {
                    self.$('.o_hr_dashboard').append(QWeb.render(template, {widget: self}));
                });
            }
            else{
                self.$('.o_hr_dashboard').append(QWeb.render('EmployeeWarning', {widget: self}));
            }
        },

        on_reverse_breadcrumb: function() {
            var self = this;
            web_client.do_push_state({});
            this.update_cp();
            this.fetch_data().then(function() {
                self.$('.o_hr_dashboard').reload();
                self.render_dashboards();
            });
        },

         update_cp: function() {
            var self = this;
         },
    });

    core.action_registry.add('crm_dashboard', DashBoard);
    return DashBoard;
});