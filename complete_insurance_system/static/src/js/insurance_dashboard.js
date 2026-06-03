/**@odoo-module **/
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
const { Component, onMounted, onWillStart,  useRef, useState } = owl
const actionRegistry = registry.category("actions");
class InsuranceDashboard extends Component {
    setup() {
        this.state = useState({
            data: {},
            insurance_data: {},
            chart: [],

        })
         this.orm = useService('orm')
         this.action = useService("action");
         this.CustomerGender = useRef("test")
         this.InsurancePolicy = useRef("insurance_policy")
         onWillStart(async () =>{
         await this._fetch_data();
         })
         onMounted(async () =>{
         this.renderChart();
         })
    }
   async _fetch_data(){
   var self = this;
   this.state.data = await this.orm.call("res.insurance" , "count_genders", [{}]);
   this.state.insurance_data = await this.orm.call("res.insurance" , "insurance_policy_count", [{}]);
   this.orm.call("res.insurance", "get_dashboard_data", [], {}).then(function(result){
           $('#total').append('<span>' + result.total_insurance + '</span>');
           $('#new').append('<span>' + result.new_insurance + '</span>');
           $('#running').append('<span>' +result.running_insurance + '</span>');
           $('#expired').append('<span>' + result.expired_insurance + '</span>');
           $('#total_claim').append('<span>' + result.total_claim + '</span>');
           $('#submit').append('<span>' + result.submitted_claim + '</span>');
           $('#approved').append('<span>' +result.approved_claim + '</span>');
           $('#rejected').append('<span>' + result.rejected_claim + '</span>');
           $('#agent').append('<span>' + result.agent_count + '</span>');
           $('#categories').append('<span>' + result.categories_count + '</span>');
           $('#sub_categories').append('<span>' + result.sub_categories_count + '</span>');
           $('#insurance_policy').append('<span>' + result.insurance_policy + '</span>');
           });
       };
       async renderChart(){
       this.charts(this.CustomerGender.el,'bar',this.state.data['products'],'Customer Gender',this.state.data['count'])
       this.charts(this.InsurancePolicy.el,'bar',this.state.insurance_data['products'],'Insurance Policy',this.state.insurance_data['count'])
       }
    charts(canvas,type,labels,label,data){
/* Function for passing datas to the charts */
    this.state.chart.push(new Chart(
        canvas,
        {
            type:type,
            data: {
                labels: labels,
                datasets: [
                    {
                    label: label,
                    data: data,
                    }
                ]
            },
        }
    ))
}
totalInsurance(){
this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'Total Insurance',
            res_model: 'res.insurance',
            view_mode: 'tree,form',
            context: {"create": false},
            views: [[false, 'list'], [false, 'form']],
        })
}
newInsurance(){
this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'New Insurance',
            res_model: 'res.insurance',
            view_mode: 'tree,form',
            context: {"create": false},
            views: [[false, 'list'], [false, 'form']],
            domain: [['state', '=', 'new']],
        })
}
runningInsurance(){
this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'New Insurance',
            res_model: 'res.insurance',
            view_mode: 'tree,form',
            context: {"create": false},
            views: [[false, 'list'], [false, 'form']],
            domain: [['state', '=', 'running']],
        })
}
expiredInsurance(){
this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'New Insurance',
            res_model: 'res.insurance',
            view_mode: 'tree,form',
            context: {"create": false},
            views: [[false, 'list'], [false, 'form']],
            domain: [['state', '=', 'expired']],
        })
}
totalClaim(){
this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'Total Claim',
            res_model: 'insurance.claim',
            view_mode: 'tree,form',
            context: {"create": false},
            views: [[false, 'list'], [false, 'form']],
        })
}
submitClaim(){
this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'Submit Claim',
            res_model: 'insurance.claim',
            view_mode: 'tree,form',
            context: {"create": false},
            views: [[false, 'list'], [false, 'form']],
            domain: [['state', '=', 'submit']],
        })
}
approveClaim(){
this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'Approved Claim',
            res_model: 'insurance.claim',
            view_mode: 'tree,form',
            context: {"create": false},
            views: [[false, 'list'], [false, 'form']],
            domain: [['state', '=', 'approved']],
        })
}
rejectedClaim(){
this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'Rejected Claim',
            res_model: 'insurance.claim',
            view_mode: 'tree,form',
            context: {"create": false},
            views: [[false, 'list'], [false, 'form']],
            domain: [['state', '=', 'rejected']],
        })
}
Agent(){
this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'Agents',
            res_model: 'res.partner',
            view_mode: 'tree,form',
            context: {"create": false},
            views: [[false, 'kanban'],[false, 'list'], [false, 'form']],
            domain: [['agent', '=', 'True']],
        })
}
Categories(){
this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'Insurance Categories',
            res_model: 'insurance.policy.category',
            view_mode: 'tree,form',
            context: {"create": false},
            views: [[false, 'list'], [false, 'form']],
        })
}
subCategories(){
this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'Insurance Subcategories',
            res_model: 'insurance.policy.sub.category',
            view_mode: 'tree,form',
            context: {"create": false},
            views: [[false, 'list'], [false, 'form']],
        })
}
insurancePolicy(){
this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'Insurance Policy',
            res_model: 'insurance.policy',
            view_mode: 'tree,form',
            context: {"create": false},
            views: [[false, 'list'], [false, 'form']],
        })
}
}
InsuranceDashboard.template = "complete_insurance_system.InsuranceDashboard";
actionRegistry.add("insurance_dashboard_tag", InsuranceDashboard);


