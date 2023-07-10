/** @odoo-module **/

import { registry } from "@web/core/registry";
import { AnalyticDistribution } from "@analytic/components/analytic_distribution/analytic_distribution";


export class AnalyticDistributionAmount extends AnalyticDistribution {

//For saving the amount permanently in widget
    async amountChange(dist_tag, ev) {
        dist_tag.amount = this.parse(ev.target.value);
        let total = this.props.record.data.price_subtotal;
        let value = this.parse(ev.target.value) / total * 100;
        dist_tag.percentage = value;
        if (this.remainderByGroup(dist_tag.group_id)) {
            this.setFocusSelector(`#plan_${dist_tag.group_id} .incomplete .o_analytic_account_name`);
        }
        this.autoFill();
    }

//     For saving the amount permanently in widget
    async formatData(nextProps) {
        const price= nextProps.record.data.price_subtotal
        const data = nextProps.value;
        const analytic_account_ids = Object.keys(data).map((id) => parseInt(id));
        const records = analytic_account_ids.length ? await this.fetchAnalyticAccounts([["id", "in", analytic_account_ids]]) : [];
        if (records.length < data.length) {
            console.log('removing tags... value should be updated');
        }
        let widgetData = Object.assign({}, ...this.allPlans.map((plan) => ({[plan.id]: {...plan, distribution: []}})));
        records.map((record) => {
            if (!widgetData[record.root_plan_id[0]]) {
                // plans might not have been retrieved
                widgetData[record.root_plan_id[0]] = { distribution: [] }
            }
            const amount = data[record.id] * price/100
            widgetData[record.root_plan_id[0]].distribution.push({
                analytic_account_id: record.id,
                percentage: data[record.id],
                amount: amount,
                id: this.nextId++,
                group_id: record.root_plan_id[0],
                analytic_account_name: record.display_name,
                color: record.color,
            });
        });

        this.state.list = widgetData;
    }
}

registry.category("fields").add("analytic_distribution_amount", AnalyticDistributionAmount);