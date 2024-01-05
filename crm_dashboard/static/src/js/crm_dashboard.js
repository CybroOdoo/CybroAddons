/** @odoo-module */
import { registry} from '@web/core/registry';
import { useService } from "@web/core/utils/hooks";
const { Component, onWillStart, onMounted} = owl
import { jsonrpc } from "@web/core/network/rpc_service";
import { _t } from "@web/core/l10n/translation";
import { session } from "@web/session";
import { WebClient } from "@web/webclient/webclient";
export class CRMDashboard extends Component {
    /**
     * Sets up the CRM Dashboard component.
     * Initializes required services and lifecycle hooks.
     */
    setup() {
        this.action = useService("action");
        this.orm = useService("orm");
        onWillStart(this.onWillStart);
        onMounted(this.onMounted);
    }
    /**
     * Function triggered before the component starts.
     * Perform necessary setup or operations here.
     */
    async onWillStart() {
        var self = this;
        this.login_employee = {};
        var def0 = jsonrpc('/web/dataset/call_kw/crm.lead/check_user_group', {
            model: 'crm.lead',
            method: 'check_user_group',
            args: [{}],
            kwargs: {},
        }).then(function(result) {
            if (result == true) {
                self.is_manager = true;
            } else {
                self.is_manager = false;
            }
        });
        var def1 = jsonrpc('/web/dataset/call_kw/crm.lead/get_upcoming_events', {
                model: "crm.lead",
                method: "get_upcoming_events",
                args: [{}],
                kwargs: {},
            })
            .then(function(res) {
                self.upcoming_events = res['event'];
                self.current_lang = res['cur_lang'];
            });
        var def2 = jsonrpc('/web/dataset/call_kw/crm.lead/get_top_deals', {
                model: "crm.lead",
                method: "get_top_deals",
                args: [{}],
                kwargs: {},
            })
            .then(function(res) {
                self.top_deals = res['deals'];
            });
        var def3 = jsonrpc('/web/dataset/call_kw/crm.lead/get_monthly_goal', {
                model: "crm.lead",
                method: "get_monthly_goal",
                args: [{}],
                kwargs: {},
            })
            .then(function(res) {
                self.monthly_goals = res['goals'];
            });
        var def4 = jsonrpc('/web/dataset/call_kw/crm.lead/get_top_sp_revenue', {
                model: "crm.lead",
                method: "get_top_sp_revenue",
                args: [{}],
                kwargs: {},
            })
            .then(function(res) {
                self.top_sp_revenue = res['top_revenue'];
            });
        var def5 = jsonrpc('/web/dataset/call_kw/crm.lead/get_country_revenue', {
                model: "crm.lead",
                method: "get_country_revenue",
                args: [{}],
                kwargs: {},
            })
            .then(function(res) {
                self.top_country_revenue = res['country_revenue'];
            });
        var def6 = jsonrpc('/web/dataset/call_kw/crm.lead/get_country_count', {
                model: "crm.lead",
                method: "get_country_count",
                args: [{}],
                kwargs: {},
            })
            .then(function(res) {
                self.top_country_count = res['country_count'];
            });
        var def8 = jsonrpc('/web/dataset/call_kw/crm.lead/get_ratio_based_country', {
                model: "crm.lead",
                method: "get_ratio_based_country",
                args: [{}],
                kwargs: {},
            })
            .then(function(res) {
                self.top_country_wise_ratio = res['country_wise_ratio'];
            });
        var def9 = jsonrpc('/web/dataset/call_kw/crm.lead/get_ratio_based_sp', {
                model: "crm.lead",
                method: "get_ratio_based_sp",
                args: [{}],
                kwargs: {},
            })
            .then(function(res) {
                self.top_salesperson_wise_ratio = res['salesperson_wise_ratio'];
            });
        var def10 = jsonrpc('/web/dataset/call_kw/crm.lead/get_ratio_based_sales_team', {
                model: "crm.lead",
                method: "get_ratio_based_sales_team",
                args: [{}],
                kwargs: {},
            })
            .then(function(res) {
                self.top_sales_team_wise_ratio = res['sales_team_wise_ratio'];
            });
        var def11 = jsonrpc('/web/dataset/call_kw/crm.lead/get_recent_activities', {
                model: "crm.lead",
                method: "get_recent_activities",
                args: [{}],
                kwargs: {},
            })
            .then(function(res) {
                self.recent_activities = res['activities'];
            });
        var def12 = jsonrpc('/web/dataset/call_kw/crm.lead/get_count_unassigned', {
                model: "crm.lead",
                method: "get_count_unassigned",
                args: [{}],
                kwargs: {},
            })
            .then(function(res) {
                self.get_count_unassigned = res['count_unassigned'];
            });
        var def13 = jsonrpc('/web/dataset/call_kw/crm.lead/get_top_sp_by_invoice', {
                model: "crm.lead",
                method: "get_top_sp_by_invoice",
                args: [{}],
                kwargs: {},
            })
            .then(function(res) {
                self.top_sp_by_invoice = res['sales_person_invoice'];
            });
        return $.when(def0, def1, def2, def3, def4, def5, def6, def8, def9, def10, def11, def12, def13);
    }
    /**
     * Handles the change event for income and expense values.
     * @param {Event} e - The event object.
     */
    on_change_income_expense_values(e) {
        e.stopPropagation();
        var $target = $(e.target);
        var value = $target.val();
        if (value == "this_year") {
            this.onclick_this_year($target.val());
        } else if (value == "this_quarter") {
            this.onclick_this_quarter($target.val());
        } else if (value == "this_month") {
            this.onclick_this_month($target.val());
        } else if (value == "this_week") {
            this.onclick_this_week($target.val());
        }
    }
    /**
     * Handles the click event for the 'this_week' option.
     * Calls a JSON-RPC method to retrieve data for the current week.
     * Updates the UI to display the relevant information.
     * @param {Event} ev - The event object.
     */
    onclick_this_week(ev) {
        var self = this;
        jsonrpc('/web/dataset/call_kw/crm.lead/crm_week', {
                model: 'crm.lead',
                method: 'crm_week',
                args: [{}],
                kwargs: {},
            })
            .then(function(result) {
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
    }
    /**
     * Handles the click event for the 'this_month' option.
     * Calls a JSON-RPC method to retrieve data for the current month.
     * Updates the UI to display the relevant information.
     * @param {Event} ev - The event object.
     */
    onclick_this_month(ev) {
        var self = this;
        jsonrpc('/web/dataset/call_kw/crm.lead/crm_month', {
                model: 'crm.lead',
                method: 'crm_month',
                args: [{}],
                kwargs: {},
            })
            .then(function(result) {
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
                $('#avg_time_this_month').append('<span>' + result.avg_time + '&nbspsec' + '</span>');
                $('#total_revenue_this_month').append('<span>' + result.opportunity_ratio_value + '</span>');
            })
    }
    /**
     * Handles the click event for the 'this_quarter' option.
     * Calls a JSON-RPC method to retrieve data for the current quarter.
     * Updates the UI to display the relevant information.
     * @param {Event} ev - The event object.
     */
    onclick_this_quarter(ev) {
        var self = this;
        jsonrpc('/web/dataset/call_kw/crm.lead/crm_quarter', {
                model: 'crm.lead',
                method: 'crm_quarter',
                args: [{}],
                kwargs: {},
            })
            .then(function(result) {
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
                $('#avg_time_this_quarter').append('<span>' + result.avg_time + '&nbspsec' + '</span>');
                $('#total_revenue_this_quarter').append('<span>' + result.opportunity_ratio_value + '</span>');
            })
    }
    /**
     * Handles the click event for the 'this_year' option.
     * Calls a JSON-RPC method to retrieve data for the current year.
     * Updates the UI to display the relevant information.
     * @param {Event} ev - The event object.
     */
    onclick_this_year(ev) {
        var self = this;
        jsonrpc('/web/dataset/call_kw/crm.lead/crm_year', {
                model: 'crm.lead',
                method: 'crm_year',
                args: [{}],
                kwargs: {},
            })
            .then(function(result) {
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
    }
    /**
     * Handles the revenue card action.
     * Initiates an action to display revenue-related data.
     * @param {Event} e - The event object.
     */
    revenue_card(e) {
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        this.action.doAction({
            name: _t("Revenue"),
            type: 'ir.actions.act_window',
            res_model: 'crm.lead',
            view_mode: 'tree,form,calendar',
            views: [
                [false, 'list'],
                [false, 'form']
            ],
            domain: [
                ['user_id', '=', session.uid],
                ['type', '=', 'opportunity'],
                ['stage_id', '=', 4]
            ],
            target: 'current',
        }, options)
    }
    /**
     * Initiates an action to display expected revenue data.
     * @param {Event} e - The event object.
     */
    exp_revenue(e) {
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        this.action.doAction({
            name: _t("Expected Revenue"),
            type: 'ir.actions.act_window',
            res_model: 'crm.lead',
            view_mode: 'tree,form,calendar',
            views: [
                [false, 'list'],
                [false, 'form']
            ],
            domain: [
                ['user_id', '=', session.uid],
                ['type', '=', 'opportunity'],
                ['active', '=', true]
            ],
            target: 'current',
        }, options)
    }
    /**
     * Initiates an action to display unassigned leads data.
     * @param {Event} e - The event object.
     */
    unassigned_leads(e) {
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        this.action.doAction({
            name: _t("Unassigned Leads"),
            type: 'ir.actions.act_window',
            res_model: 'crm.lead',
            view_mode: 'tree,form,calendar',
            views: [
                [false, 'list'],
                [false, 'form']
            ],
            domain: [
                ['user_id', '=', false],
                ['type', '=', 'lead']
            ],
            context: {
                'group_by': 'team_id'
            },
            target: 'current',
        }, options)
    }
    /**
     * Initiates an action to display opportunity data.
     * @param {Event} e - The event object.
     */
    opportunity(e) {
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        this.action.doAction({
            name: _t("Opportunity"),
            type: 'ir.actions.act_window',
            res_model: 'crm.lead',
            view_mode: 'tree,form,calendar',
            views: [
                [false, 'list'],
                [false, 'form']
            ],
            domain: [
                ['user_id', '=', session.uid],
                ['type', '=', 'opportunity']
            ],
            target: 'current',
        })
    }
    /**
     * Initiates an action to display leads assigned to the current user.
     * @param {Event} e - The event object.
     */
    my_lead(e) {
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        this.action.doAction({
            name: _t("My Leads"),
            type: 'ir.actions.act_window',
            res_model: 'crm.lead',
            view_mode: 'tree,form,calendar',
            views: [
                [false, 'list'],
                [false, 'form']
            ],
            domain: [
                ['user_id', '=', session.uid]
            ],
            target: 'current',
        }, options)
    }
    /**
     * Handles the reverse breadcrumb action.
     * Updates the breadcrumb, fetches updated data, and reloads the dashboard.
     */
    on_reverse_breadcrumb() {
        var self = this;
        WebClient.do_push_state({});
        this.update_cp();
        this.fetch_data().then(function() {
            self.$('.o_hr_dashboard').reload();
            self.render_dashboards();
        });
    }
    /**
     * Lifecycle hook triggered when the component is mounted.
     * Renders various charts and graphs upon mounting.
     */
    async onMounted() {
        this.renderElement();
        this.funnel_chart();
        this.render_annual_chart_graph();
        this.render_sales_activity_graph();
        this.render_leads_month_graph();
        this.render_revenue_count_pie();
        this.render_campaign_leads_graph();
        this.render_medium_leads_graph();
        this.render_source_leads_graph();
        this.onclick_lost_last_12months();
        this.render_lost_leads_by_stage_graph();
    }
    /**
     * Renders a doughnut chart to display lost leads categorized by stage.
     * Fetches data via JSON-RPC and generates a chart using Chart.js.
     */
    render_lost_leads_by_stage_graph() {
        var self = this
        var ctx = $(".lost_leads_by_stage_graph");
        jsonrpc('/web/dataset/call_kw/crm.lead/get_lost_lead_by_stage_pie', {
            model: "crm.lead",
            method: "get_lost_lead_by_stage_pie",
            args: [{}],
            kwargs: {},
        }).then(function(arrays) {
            var data = {
                labels: arrays[1],
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
                }, ]
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
    }
    /**
     * Handles the change event for the total lost CRM selection.
     * Determines the selected timeframe and triggers the respective method.
     * @param {Event} e - The event object.
     */
    change_total_loosed_crm(e) {
        e.stopPropagation();
        var $target = $(e.target);
        var value = $target.val();
        if (value == "lost_last_12months") {
            this.onclick_lost_last_12months($target.val());
        } else if (value == "lost_last_6months") {
            this.onclick_lost_last_6months($target.val());
        } else if (value == "lost_last_month") {
            this.onclick_lost_last_month($target.val());
        }
    }
    /**
     * Handles the click event for the 'lost_last_month' option.
     * Calls a JSON-RPC method to retrieve total lost CRM data for the last month.
     * Generates a bar chart to represent the lost CRM data.
     * @param {Event} ev - The event object.
     */
    onclick_lost_last_month(ev) {
        var self = this;
        self.initial_render = true;
        jsonrpc('/web/dataset/call_kw/crm.lead/get_total_lost_crm', {
            model: "crm.lead",
            method: "get_total_lost_crm",
            args: ['1'],
            kwargs: {},
        }).then(function(result) {
            var ctx = document.getElementById("canvas").getContext('2d');
            // Define the data
            var lost_reason = result.month // Add data values to array
            var count = result.count;
            var myChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: lost_reason, //x axis
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
    }
    /**
     * Handles the click event for displaying total lost CRM data for the last 6 months.
     * Retrieves and displays the data using Chart.js in a bar chart format.
     * @param {Event} ev - The event object.
     */
    onclick_lost_last_6months(ev) {
        var self = this;
        self.initial_render = true;
        jsonrpc('/web/dataset/call_kw/crm.lead/get_total_lost_crm', {
            model: "crm.lead",
            method: "get_total_lost_crm",
            args: ['6'],
            kwargs: {},
        }).then(function(result) {
            var ctx = document.getElementById("canvas").getContext('2d');
            // Define the data
            var lost_reason = result.month // Add data values to array
            var count = result.count;
            var myChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: lost_reason, //x axis
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
    }
    /**
     * Handles the click event for displaying total lost CRM data for the last 12 months.
     * Retrieves and displays the data using Chart.js in a bar chart format.
     * If the user is a manager, it fetches data for the last 12 months.
     * @param {Event} ev - The event object.
     */
    onclick_lost_last_12months(ev) {
        var self = this;
        if (self.is_manager == true) {
            self.initial_render = true;
            jsonrpc('/web/dataset/call_kw/crm.lead/get_total_lost_crm', {
                model: "crm.lead",
                method: "get_total_lost_crm",
                args: ['12'],
                kwargs: {},
            }).then(function(result) {
                var ctx = document.getElementById("canvas").getContext('2d');
                // Define the data
                var lost_reason = result.month // Add data values to array
                var count = result.count;
                var myChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: lost_reason, //x axis
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
    }
    /**
     * Renders a doughnut chart to display lost leads categorized by reason.
     * Fetches data via JSON-RPC and generates a chart using Chart.js.
     */
    render_lost_leads_graph() {
        var self = this;
        var ctx = $(".lost_leads_graph");
        console.log(ctx)
        jsonrpc('/web/dataset/call_kw/crm.lead/get_lost_lead_by_reason_pie', {
            model: "crm.lead",
            method: "get_lost_lead_by_reason_pie",
            args: [{}],
            kwargs: {},
        }).then(function(arrays) {
            var data = {
                labels: arrays[1],
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
                }, ]
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
    }
    /**
     * Renders a doughnut chart to display leads categorized by their source.
     * Fetches data via JSON-RPC and generates a chart using Chart.js.
     */
    render_source_leads_graph() {
        var self = this
        var ctx = $(".source_lead");
        jsonrpc('/web/dataset/call_kw/crm.lead/get_the_source_pie', {
            model: "crm.lead",
            method: "get_the_source_pie",
            args: [{}],
            kwargs: {},
        }).then(function(arrays) {
            var data = {
                labels: arrays[1],
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
                }, ]
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
    }
    /**
     * Renders a doughnut chart to display leads categorized by their medium.
     * Fetches data via JSON-RPC and generates a chart using Chart.js.
     */
    render_medium_leads_graph() {
        var self = this
        var ctx = $(".medium_leads");
        jsonrpc('/web/dataset/call_kw/crm.lead/get_the_medium_pie', {
            model: "crm.lead",
            method: "get_the_medium_pie",
            args: [{}],
            kwargs: {},
        }).then(function(arrays) {
            var data = {
                labels: arrays[1],
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
                }, ]
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
    }
    /**
     * Renders a doughnut chart to display leads categorized by their campaign source.
     * Fetches data via JSON-RPC and generates a chart using Chart.js.
     */
    render_campaign_leads_graph() {
        var self = this
        var ctx = $(".campaign_source");
        jsonrpc('/web/dataset/call_kw/crm.lead/get_the_campaign_pie', {
            model: "crm.lead",
            method: "get_the_campaign_pie",
            args: [{}],
            kwargs: {},
        }).then(function(arrays) {
            var data = {
                labels: arrays[1],
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
                }, ]
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
    }
    /**
     * Renders a doughnut chart to display revenue count data.
     * Fetches data via JSON-RPC and generates a chart using Chart.js.
     */
    render_revenue_count_pie() {
        var self = this;
        var ctx = $(".revenue_count_pie_canvas");
        jsonrpc('/web/dataset/call_kw/crm.lead/revenue_count_pie', {
            model: "crm.lead",
            method: "revenue_count_pie",
            args: [{}],
            kwargs: {},
        }).then(function(arrays) {
            var data = {
                labels: arrays[1],
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
                }, ]
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
    }
    /**
     * Renders a doughnut chart to display leads created each month.
     * Fetches data via JSON-RPC and generates a chart using Chart.js.
     */
    render_leads_month_graph() {
        var self = this
        var ctx = $(".lead_month");
        jsonrpc('/web/dataset/call_kw/crm.lead/get_lead_month_pie', {
            model: "crm.lead",
            method: "get_lead_month_pie",
            args: [{}],
            kwargs: {},
        }).then(function(arrays) {
            var data = {
                labels: arrays[1],
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
                }, ]
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
    }
    /**
     * Renders a doughnut chart to display sales activity data.
     * Fetches data via JSON-RPC and generates a chart using Chart.js.
     */
    render_sales_activity_graph() {
        var self = this
        var ctx = $(".sales_activity");
        jsonrpc('/web/dataset/call_kw/crm.lead/get_the_sales_activity', {
            model: "crm.lead",
            method: "get_the_sales_activity",
            args: [{}],
            kwargs: {},
        }).then(function(arrays) {
            var data = {
                labels: arrays[1],
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
                }, ]
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
    }
    /**
     * Renders a bar chart to display annual target data.
     * Fetches data via JSON-RPC and generates a chart using Chart.js.
     */
    render_annual_chart_graph() {
        var self = this
        var ctx = $(".annual_target");
        jsonrpc('/web/dataset/call_kw/crm.lead/get_the_annual_target', {
            model: "crm.lead",
            method: "get_the_annual_target",
            args: [{}],
            kwargs: {},
        }).then(function(arrays) {
            var data = {
                labels: arrays[1],
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
                }, ]
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
                    responsive: true,
                    maintainAspectRatio: false,
                    legend: {
                        display: false //This will do the task
                    },
                }
            });
        });
    }
    /**
     * Renders a funnel chart displaying lead stage data.
     * Fetches data via JSON-RPC and generates a chart using Highcharts.
     */
    funnel_chart() {
        jsonrpc('/web/dataset/call_kw/crm.lead/get_lead_stage_data', {
            model: "crm.lead",
            method: "get_lead_stage_data",
            args: [{}],
            kwargs: {},
        }).then(function(callbacks) {
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
                series: [{
                    name: "Number Of Leads",
                    data: callbacks,
                }],
            });
        });
    }
    /**
     * Fetches lead details via JSON-RPC and appends the data to specific HTML elements.
     */
    renderElement(ev) {
        var self = this;
        jsonrpc('/web/dataset/call_kw/crm.lead/lead_details_user', {
            model: "crm.lead",
            method: "lead_details_user",
            args: [{}],
            kwargs: {},
        }).then(function(result) {
            $('#leads_this_month').append('<span>' + result.record + '</span>');
            $('#opp_this_month').append('<span>' + result.record_op + '</span>');
            $('#exp_rev_this_month').append('<span>' + self.monthly_goals[2] + '&nbsp' + result.record_rev_exp + '</span>');
            $('#rev_this_month').append('<span>' + self.monthly_goals[2] + '&nbsp' + result.record_rev + '</span>');
            $('#ratio_this_month').append('<span>' + result.record_ratio + '</span>');
            $('#avg_time_this_month').append('<span>' + result.avg_time + '&nbspsec' + '</span>');
            $('#total_revenue_this_month').append('<span>' + result.opportunity_ratio_value + '</span>');
            $('#target').append('<span>' + result.target + '</span>');
            $('#ytd_target').append('<span>' + result.ytd_target + '</span>');
            $('#difference').append('<span>' + result.difference + '</span>');
            $('#won').append('<span>' + result.won + '</span>');
        })
    }
}
CRMDashboard.template = "CRMdashboard"
registry.category("actions").add("crm_dashboard", CRMDashboard)
