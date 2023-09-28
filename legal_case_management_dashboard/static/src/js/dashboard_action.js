odoo.define('legal_case_management_dashboard.case_dashboard', function(require) {
    "use strict";
    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var rpc = require('web.rpc');
    var ajax = require('web.ajax');
    var _t = core._t;
    var cases_list;
    var trial_list;
    var evidence_list;
    var lawyer_list;
    var client_list;
    var total_client;
    var CaseDashBoard = AbstractAction.extend({
        contentTemplate: 'CaseDashBoard',
        events: {
            'click #total_case': '_OnClickTotalCase',
            'click #total_trials': '_OnClickTotalTrials',
            'click #total_evidences': '_OnClickTotalEvidences',
            'click #total_lawyers': '_OnClickTotalLawyers',
            'click #total_clients': '_OnClickTotalClients',
            'change #lawyer_wise': '_OnchangeSelection',
            'change #stage_wise': '_OnchangeSelection',
            'change #month_wise': '_OnchangeSelection',
        },
        // Click function of case card
        _OnClickTotalCase: function(e) {
            if (cases_list) {
                this.do_action({
                    name: _t("Total Cases"),
                    type: 'ir.actions.act_window',
                    res_model: 'case.registration',
                    view_mode: 'tree,form',
                    views: [
                        [false, 'list'],
                        [false, 'form']
                    ],
                    domain: [
                        ['id', 'in', cases_list]
                    ],
                    context: {
                        create: false
                    },
                    target: 'current',
                })
            } else {
                this.do_action({
                    name: _t("Total Cases"),
                    type: 'ir.actions.act_window',
                    res_model: 'case.registration',
                    view_mode: 'tree,form',
                    views: [
                        [false, 'list'],
                        [false, 'form']
                    ],
                    context: {
                        create: false
                    },
                    target: 'current',
                })
            }
        },
        // Click function of trial card
        _OnClickTotalTrials: function(e) {
            if (trial_list) {
                this.do_action({
                    name: _t("Total Trials"),
                    type: 'ir.actions.act_window',
                    res_model: 'legal.trial',
                    view_mode: 'tree,form',
                    views: [
                        [false, 'list'],
                        [false, 'form']
                    ],
                    domain: [
                        ['id', 'in', trial_list]
                    ],
                    context: {
                        create: false
                    },
                    target: 'current',
                })
            } else {
                this.do_action({
                    name: _t("Total Trials"),
                    type: 'ir.actions.act_window',
                    res_model: 'legal.trial',
                    view_mode: 'tree,form',
                    views: [
                        [false, 'list'],
                        [false, 'form']
                    ],
                    context: {
                        create: false
                    },
                    target: 'current',
                })
            }
        },
        // Click function of evidence card
        _OnClickTotalEvidences: function(e) {
            if (evidence_list) {
                this.do_action({
                    name: _t("Total Evidences"),
                    type: 'ir.actions.act_window',
                    res_model: 'legal.evidence',
                    view_mode: 'tree,form',
                    views: [
                        [false, 'list'],
                        [false, 'form']
                    ],
                    domain: [
                        ['id', 'in', evidence_list]
                    ],
                    context: {
                        create: false
                    },
                    target: 'current',
                })
            } else {
                this.do_action({
                    name: _t("Total Evidences"),
                    type: 'ir.actions.act_window',
                    res_model: 'legal.evidence',
                    view_mode: 'tree,form',
                    views: [
                        [false, 'list'],
                        [false, 'form']
                    ],
                    context: {
                        create: false
                    },
                    target: 'current',
                })
            }
        },
        //Click function of lawyers card
        _OnClickTotalLawyers: function(e) {
            if (lawyer_list) {
                this.do_action({
                    name: _t("Total Lawyers"),
                    type: 'ir.actions.act_window',
                    res_model: 'hr.employee',
                    view_mode: 'tree,form',
                    views: [
                        [false, 'list'],
                        [false, 'form']
                    ],
                    domain: [
                        ['id', 'in', lawyer_list]
                    ],
                    context: {
                        create: false
                    },
                    target: 'current',
                })
            } else {
                this.do_action({
                    name: _t("Total Lawyers"),
                    type: 'ir.actions.act_window',
                    res_model: 'hr.employee',
                    view_mode: 'tree,form',
                    views: [
                        [false, 'list'],
                        [false, 'form']
                    ],
                    domain: [
                        ['is_lawyer', '=', true],
                        ['parent_id', '=', false]
                    ],
                    context: {
                        create: false
                    },
                    target: 'current',
                })
            }
        },
        // Click function of clients card
        _OnClickTotalClients: function(e) {
            if (client_list) {
                this.do_action({
                    name: _t("Total Clients"),
                    type: 'ir.actions.act_window',
                    res_model: 'res.partner',
                    view_mode: 'tree,form',
                    views: [
                        [false, 'list'],
                        [false, 'form']
                    ],
                    domain: [
                        ['id', 'in', client_list]
                    ],
                    context: {
                        create: false
                    },
                    target: 'current',
                })
            } else if (total_client) {
                this.do_action({
                    name: _t("Total Clients"),
                    type: 'ir.actions.act_window',
                    res_model: 'res.partner',
                    view_mode: 'tree,form',
                    views: [
                        [false, 'list'],
                        [false, 'form']
                    ],
                    domain: [
                        ['id', 'in', total_client]
                    ],
                    context: {
                        create: false
                    },
                    target: 'current',
                })
            }
        },
        // Onchange filters
        _OnchangeSelection: function() {
            var lawyer_filter = $('#lawyer_wise')
                .val()
            var stage_filter = $('#stage_wise')
                .val()
            var date_filter = $('#month_wise')
                .val()
            var data = {
                'stage': stage_filter,
                'lawyer': lawyer_filter,
                'month_wise': date_filter
            }
            ajax.jsonRpc('/dashboard/filter', 'call', {
                    'data': data
                })
                .then(function(value) {
                    cases_list = value.total_case
                    trial_list = value.trials
                    evidence_list = value.evidences
                    lawyer_list = value.lawyers
                    client_list = value.clients
                    document.getElementById("total_cases")
                        .innerHTML = value.total_case.length;
                    document.getElementById("total_invoices")
                        .innerHTML = value.total_invoiced;
                    document.getElementById("trials_count")
                        .innerHTML = value.trials.length;
                    document.getElementById("evidences_count")
                        .innerHTML = value.evidences.length;
                    document.getElementById("lawyers_count")
                        .innerHTML = value.lawyers.length;
                    document.getElementById("clients_count")
                        .innerHTML = value.clients.length;
                })
        },
        CaseManagementDashboard: {},
        //Get datas to dashboard while opening the dashboard
        willStart: function() {
            var self =this;
            var promise = ajax.rpc('/case/dashboard', {})
                .then((result) => {
                    this.CaseManagementDashboard = result;
                    total_client = result.clients_in_case
                    //Graphs starts here
                    google.charts.load('current', {
                        'packages': ['corechart']
                    });
                    google.charts.setOnLoadCallback(drawChart);
                    function drawChart() {
                    try{
                        //  Pie chart starts
                        var data = google.visualization.arrayToDataTable(result['case_category']);
                        var optionss = {
                            'backgroundColor': 'transparent',
                            is3D: true
                        };
                        var chart = new google.visualization.PieChart(document.getElementById('pie_chart'));
                        chart.draw(data, optionss);
                        // Pie chart end
                        //Donut chart start
                        var datas = google.visualization.arrayToDataTable(result.top_10_cases);
                        var options = {
                            'backgroundColor': 'transparent',
                            pieHole: 0.5
                        };
                        var charts = new google.visualization.PieChart(document.getElementById('donut_chart'));
                        charts.draw(datas, options);
                        //Donut chart end
                        //Linechart start
                        var datas = google.visualization.arrayToDataTable(result['data_list']);
                        var optionss = {
                            'backgroundColor': 'transparent',
                            legend: 'none',
                            bar: {
                                groupWidth: "40%"
                            },
                        };
                        var charts = new google.visualization.LineChart(document.getElementById('mygraph'));
                        charts.draw(datas, optionss);
                        //Linechart end
                        //Column chart start
                        var column_data = google.visualization.arrayToDataTable(result.stage_count);
                        var column_options = {
                            'backgroundColor': 'transparent',
                            legend: 'none',
                            bar: {
                                groupWidth: "40%"
                            },
                        };
                        var column_chart = new google.visualization.ColumnChart(document.getElementById('column_graph'));
                        column_chart.draw(column_data, column_options);
                        //column chart end
                        }catch (e) {
                        self.willStart()
                    }
                    }
                });
            return Promise.all([
                this._super.apply(this, arguments), promise
            ]);
         },
        //Set a title for the dashboard and call the function which adds the
        //lawyer's to the lawyer selection field
        start: function() {
            var self = this;
            this.set("title", 'Dashboard');
            return this._super()
                .then(function() {
                    self.render_filter();
                });
        },
        render_filter: function() {
            //Add lawyers to lawyers selection field
            ajax.rpc('/selection/field/lawyer', {})
                .then((result) => {
                    var lawyer_list = result
                    $(lawyer_list)
                        .each(function(lawyer) {
                            $('#lawyer_wise')
                                .append("<option value=" + lawyer_list[lawyer].id + ">" + lawyer_list[lawyer].name + "</option>");
                        });
                })
        },
    })
    core.action_registry.add('case_dashboard_tags', CaseDashBoard);
    return CaseDashBoard;
})
