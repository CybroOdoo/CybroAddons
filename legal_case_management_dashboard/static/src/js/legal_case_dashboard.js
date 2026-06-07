/** @odoo-module */

/**
 * Legal Case Management Dashboard
 *
 * This file defines the OWL component responsible for rendering the
 * Legal Case Management Dashboard. It handles data fetching, filtering,
 * and visualization of case-related information using charts and metrics.
 */

import { registry} from '@web/core/registry';
import { useService } from "@web/core/utils/hooks";
const { Component, onWillStart, onMounted , useState , useRef } = owl
import { rpc } from "@web/core/network/rpc";
import { _t } from "@web/core/l10n/translation";

export class LegalCaseDashBoard extends Component {
    /**
     * Initialize component state, services, and references.
     */
	setup() {
        // Safe access to company service
        try {
            this.companyService = useService("company");
        } catch (e) {
            console.warn("Company service not available. Using fallback id=1");
            this.companyService = { currentCompany: { id: 1 } };
        }

        this.action = useService("action");
        this.orm = useService("orm");
        this.rpc = this.env.services.rpc;
        this.lawyer_wise = useRef('lawyer_wise');

        this.state = useState({
            lawyer: 'admin',
            stage:  null,
            month: null,
            cases_list: [],
            trial_list: [],
            evidence_list: [],
            lawyer_list: [],
            client_list: [],
            total_client: [],
            case_count: 0,
            invoice_count: 0,
            trials_count: 0,
            evidences_count: 0,
            lawyers_count: 0,
            clients_count: 0,
        });
        /**
         * Fetches initial dashboard data and loads default values
         * without applying any filters.
         */
        onWillStart(async () => {
            await this.fetchData();
            await this._onWithoutFilter();
        });
        /**
         * Fetches lawyer selection data from the backend and dynamically
         * populates the lawyer dropdown field.
         */
        onMounted(() => {
            rpc('/selection/field/lawyer')
            .then((result) => {
                var selection = this.lawyer_wise.el;
                result.forEach(lawyer => {
                    const option = document.createElement('option');
                    option.value = lawyer.id;
                    option.textContent = lawyer.name;
                    selection.appendChild(option);
                });
            }).catch(error => {
                console.error(error);
            });
        });
    }

    /**
     * Fetch dashboard data and render charts.
     */
	fetchData(){
        rpc('/case/dashboard', {'current_company_id': this.companyService.currentCompany.id})
            .then((result) => {
                this.CaseManagementDashboard = result;
                this.state.total_client = result.clients_in_case
                //Graphs starts here
                google.charts.load('current', {
                    'packages': ['corechart']
                });
                google.charts.setOnLoadCallback(drawChart);
                function drawChart() {
                    try{
                    //  Pie chart starts
                    var pieData = google.visualization.arrayToDataTable(result['case_category']);
                    var pieOptions = {
                        'backgroundColor': 'transparent',
                        is3D: true
                    };
                    var pieChart = new google.visualization.PieChart(document.getElementById('pie_chart'));
                    pieChart.draw(pieData, pieOptions);
                    // Pie chart end
                    //Donut chart start
                    var donutData = google.visualization.arrayToDataTable(result.top_10_cases);
                    var donutOptions = {
                        'backgroundColor': 'transparent',
                        pieHole: 0.5
                    };
                    var donutChart = new google.visualization.PieChart(document.getElementById('donut_chart'));
                    donutChart.draw(donutData, donutOptions);
                    //Donut chart end
                    //Linechart start
                    var lineData = google.visualization.arrayToDataTable(result['data_list']);
                    var lineOptions = {
                        'backgroundColor': 'transparent',
                        legend: 'none',
                        line: {
                            groupWidth: "40%"
                        },
                    };
                    var lineChart = new google.visualization.LineChart(document.getElementById('mygraph'));
                    lineChart.draw(lineData, lineOptions);
                    //Linechart end
                    //Column chart start
                    var columnData = google.visualization.arrayToDataTable(result.stage_count);
                    var columnOptions = {
                        'backgroundColor': 'transparent',
                        legend: 'none',
                        bar: {
                            groupWidth: "40%"
                        },
                    };
                    var columnChart = new google.visualization.ColumnChart(document.getElementById('column_graph'));
                    columnChart.draw(columnData, columnOptions);
                    //column chart end
                    }
                    catch (e) {
                        console.error("Chart error:", e);
                    }
                }
            }).catch(error => {
                console.error(error);
            });
	}
    /**
     * Load dashboard values without filters
     */
	_onWithoutFilter(){
	    rpc('/dashboard/without/filter',  {
	        'current_company_id': this.companyService.currentCompany.id
            })
            .then((value) => {
                this.state.case_count = value.total_case;
                this.state.invoice_count = value.total_invoiced;
                this.state.trials_count = value.trials;
                this.state.evidences_count = value.evidences;
                this.state.lawyers_count = value.lawyers;
                this.state.clients_count = value.clients;
            }).catch(error => {
                console.error(error);
            });
	}
    /**
     * Handle filter changes for stage, lawyer, and date.
     */
	_onChangeStageFilter(ev){
        //	Values loaded by changing the stage filter
        var lawyer_filter = this.state.lawyer
        var stage_filter = this.state.stage
        var date_filter = this.state.month
        var data = {
            'stage': stage_filter,
            'lawyer': lawyer_filter || 'admin',
            'month_wise': date_filter
        };
       rpc('/dashboard/filter',  {
                'data': data,
                'current_company_id': this.companyService.currentCompany.id
            })
            .then((value) => {
                this.state.cases_list = value.total_case
                this.state.trial_list = value.trials
                this.state.evidence_list = value.evidences
                this.state.lawyer_list = value.lawyers
                this.state.client_list = value.clients
                this.state.case_count = value.total_case.length;
                this.state.invoice_count = value.total_invoiced;
                this.state.trials_count = value.trials.length;
                this.state.evidences_count = value.evidences.length;
                this.state.lawyers_count = value.lawyers.length;
                this.state.clients_count = value.clients.length;
            }).catch(error => {
                console.error(error);
            });
	}
    /**
     * Open list view of clients.
     * Navigates to the client list view, filtered based on selected
     * client IDs or current company context.
     */
	_onClickTotalClients() {
        let domain = [];
        if (this.state.client_list && this.state.client_list.length > 0) {
            domain = [['id', 'in', this.state.client_list]];
        } else {
            const currentCompanyId = this.companyService.currentCompany.id;
            domain = ['|',
                ['company_id', '=', false],
                ['company_id', '=', currentCompanyId]
            ];
        }
        this.action.doAction({
            name: _t("Total Clients"),
            type: 'ir.actions.act_window',
            res_model: 'res.partner',
            view_mode: 'tree,form',
            views: [
                [false, 'list'],
                [false, 'form']
            ],
            domain: domain,
            context: { create: false },
            target: 'current',
        });
    }
    /**
     * Open list view of trials.
     *
     * Navigates to the trial records filtered by selected trial IDs.
     */
    _onClickTotalTrials() {
        // Loading the total trials for the cases
        this.action.doAction({
            name: _t("Total Trials"),
            type: 'ir.actions.act_window',
            res_model: 'legal.trial',
            view_mode: 'list,form',
            views: [
                [false, 'list'],
                [false, 'form']
            ],
            domain: this.state.trial_list && this.state.trial_list.length > 0 ? [['id', 'in', this.state.trial_list]] : [],
            context: { create: false },
            target: 'current',
        });
    }
    /**
     * Open list view of lawyers.
     *
     * Displays lawyer records filtered by selected IDs or shows
     * all lawyers if no filter is applied.
     */
    _onClickTotalLawyers() {
        // Load the lawyer lists
        let actionConfig = {
            name: _t("Total Lawyers"),
            type: 'ir.actions.act_window',
            res_model: 'hr.employee',
            view_mode: 'list,form',
            views: [
                [false, 'list'],
                [false, 'form']
            ],
            context: {
                create: false
            },
            target: 'current',
        };
        actionConfig.domain = this.state.lawyer_list.length > 0 ? [['id', 'in', this.state.lawyer_list]] : [['is_lawyer', '=', true]];
        this.action.doAction(actionConfig);
    }
    /**
     * Open list view of evidences.
     *
     * Displays evidence records filtered by selected evidence IDs.
     */
    _onClickTotalEvidences() {
        // Load the total evidences
        let actionConfig = {
            name: _t("Total Evidences"),
            type: 'ir.actions.act_window',
            res_model: 'legal.evidence',
            view_mode: 'list,form',
            views: [
                [false, 'list'],
                [false, 'form']
            ],
            context: {
                create: false
            },
            target: 'current',
        };
        actionConfig.domain = this.state.evidence_list && this.state.evidence_list.length > 0 ? [['id', 'in', this.state.evidence_list]] : [] ;
        this.action.doAction(actionConfig);
    }
    /**
     * Open list view of cases.
     *
     * Displays case records filtered by selected case IDs.
     */
	_onClickTotalCase() {
        // Load the total case
        let actionConfig = {
            name: _t("Total Cases"),
            type: 'ir.actions.act_window',
            res_model: 'case.registration',
            view_mode: 'list,form',
            views: [
                [false, 'list'],
                [false, 'form']
            ],
            context: {
                create: false
            },
            target: 'current',
        };
        actionConfig.domain = this.state.cases_list && this.state.cases_list.length > 0  ? [['id', 'in', this.state.cases_list]] : [];
        this.action.doAction(actionConfig);
    }
}
LegalCaseDashBoard.template = "LegalCaseDashBoard"
registry.category("actions").add("case_dashboard_tags", LegalCaseDashBoard)
