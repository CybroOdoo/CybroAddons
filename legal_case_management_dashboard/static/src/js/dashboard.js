/** @odoo-module */
import { registry} from '@web/core/registry';
import { useService } from "@web/core/utils/hooks";
const { Component, onWillStart, onMounted , useState } = owl
import { jsonrpc } from "@web/core/network/rpc_service";
import { _t } from "@web/core/l10n/translation";
import { useRef } from "@odoo/owl";
var cases_list;
var trial_list;
var evidence_list;
var lawyer_list;
var client_list;
var total_client;

export class LegalDashboard extends Component {
    /**
     * Setup method to initialize required services and register event handlers.
     */
	setup() {
		this.action = useService("action");
		this.orm = useService("orm");
		this.rpc = this.env.services.rpc
		this.case_state = useState({
            // Unfold the main MO's operations by default
            case_count: 0,
            invoice_count: 0,
            trials_count:0,
            evidences_count:0,
            lawyers_count:0,
            clients_count:0,
        });
		onWillStart(this.onWillStart);
		onMounted(this.onMounted);

	}
	async onWillStart() {
		await this.fetch_data();
		await this._onWithoutFilter();

	}
	async onMounted() {
		// Render other components after fetching data
		this.render_filter();
	}

	render_filter(){
	    //Add lawyers to lawyers selection field
        jsonrpc('/selection/field/lawyer')
            .then((result) => {
                var lawyer_list = result
                $(lawyer_list).each(function(lawyer) {
                        $('#lawyer_wise').append("<option value=" + lawyer_list[lawyer].id + ">" + lawyer_list[lawyer].name + "</option>");
                    });
            })
	}
//	CaseManagementDashboard: {},
	fetch_data(){
	    var self =this;
            var promise = jsonrpc('/case/dashboard', {})
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
                        var chart_options = {
                            'backgroundColor': 'transparent',
                            is3D: true
                        };
                        var chart = new google.visualization.PieChart(document.getElementById('pie_chart'));
                        chart.draw(data, chart_options);
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
                        var line_options = {
                            'backgroundColor': 'transparent',
                            legend: 'none',
                            line: {
                                groupWidth: "40%"
                            },

                        };
                        var charts = new google.visualization.LineChart(document.getElementById('mygraph'));
                        charts.draw(datas, line_options);
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
                        }
                        catch (e) {
                            this.willStart()
                        }
                    }
                });
	}
	_onWithoutFilter(){
	    var self = this;
	    jsonrpc('/dashboard/without/filter',  {
                })
                .then(function(value) {
                    self.case_state.case_count = value.total_case;
                    self.case_state.invoice_count = value.total_invoiced;
                    self.case_state.trials_count = value.trials;
                    self.case_state.evidences_count = value.evidences;
                    self.case_state.lawyers_count = value.lawyers;
                    self.case_state.clients_count = value.clients;
                });
	}
	_onchangeStageFilter(ev){
	        var self = this;
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
           jsonrpc('/dashboard/filter',  {
                    'data': data
                })
                .then(function(value) {
                    cases_list = value.total_case
                    trial_list = value.trials
                    evidence_list = value.evidences
                    lawyer_list = value.lawyers
                    client_list = value.clients
                    self.case_state.case_count = value.total_case.length;
                    self.case_state.invoice_count = value.total_invoiced;
                    self.case_state.trials_count = value.trials.length;
                    self.case_state.evidences_count = value.evidences.length;
                    self.case_state.lawyers_count = value.lawyers.length;
                    self.case_state.clients_count = value.clients.length;
                });
	}
	_OnClickTotalClients() {
        if (client_list) {
            this.action.doAction({
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
            this.action.doAction({
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
    }
	 _OnClickTotalTrials(){
        if (trial_list) {
            this.action.doAction({
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
            this.action.doAction({
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
    }
    _OnClickTotalLawyers() {
        if (lawyer_list) {
            this.action.doAction({
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
            this.action.doAction({
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
    }
     _OnClickTotalEvidences() {
        if (evidence_list) {
            this.action.doAction({
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
            this.action.doAction({
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
     }
	_OnClickTotalCase(){
	    if (cases_list) {
            this.action.doAction({
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
            this.action.doAction({
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
	}
}
LegalDashboard.template = "CaseDashBoard"
registry.category("actions").add("case_dashboard_tags", LegalDashboard)
