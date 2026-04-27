/** @odoo-module **/
import {registry} from "@web/core/registry";
import {Component} from "@odoo/owl";
import {onWillStart, onMounted, useState, useRef, useEffect} from "@odoo/owl";
import {useService} from "@web/core/utils/hooks";

export class ManpowerDashBoard extends Component {
    setup() {
        super.setup(...arguments);
        this.orm = useService("orm");
        this.action = useService("action");
        this.Leadstage = useRef('labour_contract')
        this.LeadByMonth = useRef('contract')
        this.CrmActivities = useRef('customer_contract')
        this.LeadByCampaign = useRef('worker_availability')
        this.state = useState({
            period: 'monthly',
            leads: null,
            opportunities: null,
            exp_revenue: null,
            revenue: null,
            win_ratio: null,
            avg_close_time: null,
            opportunity_ratio: null,
            unassigned_leads: null,
            charts: [],
            upcoming_events: [],
            current_lang: [],
            top_sp_revenue: [],
            country_count: [],
            country_revenue: [],
            recent_activities:[],

            labour_supply_details: [],
            customers: [],
            total_invoiced_amount: [],
            skills: [],
            expected_amount: [],
            charts: [],

        })
        onWillStart(async () => {
            await this.fetch_data();

        });

        useEffect(() => {
            if (this.state.charts.length > 0) {
                this.state.charts.forEach(chart => {
                    chart.destroy();
                });
            }
            if (this.state.period) {
                this.render_get_contract_amount();
                this.render_get_contract_count_state();
                this.render_get_contract_count_customer();
                this.render_get_workers_count();
            }
        }, () => [this.state.period]);
    }


    async fetch_data() {
        const results = await Promise.all([
            this.orm.call('workers.details', 'get_labour_supply_details'),
            this.orm.call('workers.details', 'get_top_customer'),
            this.orm.call('workers.details', 'get_total_invoiced_amount'),
            this.orm.call('workers.details', 'get_skills_available'),
            this.orm.call('workers.details', 'get_expected_amount'),
            this.orm.call('workers.details', 'get_workers_available')
        ]);
        this.state.labour_supply_details = results[0]['ongoing_contract']
        this.state.customers = results[1]['customer']
        this.state.total_invoiced_amount = results[2]['invoiced_amount']
        this.state.skills = results[3]['skill']
        this.state.expected_amount = results[4]['expected_amount']
        this.state.workers = results[5]['workers']
    }
    
    get_graph(ctx, label, labels, datas, type, custom_colors=null) {
        let colors = custom_colors || [
            "#003f5c",
            "#2f4b7c",
            "#f95d6a",
            "#665191",
            "#d45087",
            "#ff7c43",
            "#ffa600",
            "#a05195",
            "#6d5c16"
        ];
        
        const data = {
            labels: labels,
            datasets: [{
                label: label,
                data: datas,
                backgroundColor: colors,
                borderColor: colors,
            }]
        };

        //create Chart class object
        var chart = new Chart(ctx, {
            type: type,
            data: data,

            // options: options
        });
        this.state.charts.push(chart)
    
    }


    async render_get_contract_amount() {

        var self = this;
        var ctx = this.Leadstage.el;
        const arrays = await this.orm.call('workers.details', "get_details_amount", [this.state.period]);
        this.get_graph(ctx, 'Hide', arrays.sequence, arrays.amount, 'bar')

    }

    async render_get_contract_count_state() {

        var self = this;
        var ctx = this.LeadByMonth.el;
        const arrays = await this.orm.call('workers.details', "get_contract_count_state", []);
        this.get_graph(ctx, 'State', arrays.state, arrays.count, 'line')

    }

    async render_get_contract_count_customer() {

        var self = this;
        var ctx = this.CrmActivities.el;
        const arrays = await this.orm.call('workers.details', "get_contract_count_customer", []);
        this.get_graph(ctx, 'Customer', arrays.name, arrays.count, 'bar')
    }

    async render_get_workers_count() {

        var self = this;
        var ctx = this.LeadByCampaign.el;
        const arrays = await this.orm.call('workers.details', "get_workers_count", []);
        this.get_graph(ctx, 'Workers', arrays.state, arrays.count, 'doughnut', ["#000000", "#FFC107"])
    }

}
ManpowerDashBoard.template = 'DashboardLabourSupply'
registry.category("actions").add("labour_supply_dashboard", ManpowerDashBoard)
