/**@odoo-module **/

import { Component,onWillStart,onMounted,useRef,useState } from "@odoo/owl";
import { loadBundle } from "@web/core/assets";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks"
import { session } from "@web/session";
const actionRegistry = registry.category("actions");

class RenewableEnergyDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");

        this.inputFilterBy=useRef("filter_by_input");
        this.inputFilterByMonth=useRef("filter_by_month");
        this.inputFilterByWeek=useRef("filter_by_week");

        this.subcontractFilter=useRef("subcontract_filter");
        this.internalFilter=useRef("internal_filter");

        this.ctx1=useRef("team_task_graph");
        this.ctx2=useRef("customer_category_graph");
        this.ctx3=useRef("crm_lead_status");

        this.renOrderCount=useRef("ren_order_count");
        this.materialOrderCount=useRef("material_order_count");
        this.materialArrivedCount=useRef("material_arrived_count")
        this.maintenanceRequestCount=useRef("maintenance_request_count");
        this.saleOrderCount=useRef("sale_order_count");
        this.orderCompletedCount=useRef("order_completed_count");
        this.inspectionNewCount=useRef("inspection_new_count");
        this.inspectionInProgressCount=useRef("inspection_in_progress_count");
        this.inspectionCompletedCount=useRef("inspection_completed_count");
        this.inspectionCancelledCount=useRef("inspection_cancelled_count");
        this.contractNewCount=useRef("subcontract_new_count");
        this.contractInProgressCount=useRef("subcontract_in_progress_count");
        this.contractCompletedCount=useRef("subcontract_completed_count");
        this.contractCancelledCount=useRef("subcontract_cancelled_count");
        this.internalNewCount=useRef("internal_new_count");
        this.internalInProgressCount=useRef("internal_in_progress_count");
        this.internalCompletedCount=useRef("internal_completed_count");
        this.internalCancelledCount=useRef("internal_cancelled_count");

        onWillStart(async () => {
                await loadBundle("web.chartjs_lib");
                const month = ["January","February","March","April","May","June","July","August","September","October","November","December"];
                var Today = new Date();
                this.data = await this.orm.call('ren.order','get_dashboard_details',[[]],{})
                this.props.months=month.slice(0,Today.getMonth()+1).map((x,ind)=>[ind,x])
                this.props.noOfWeeks=Array.from({length: Math.round((Today - new Date(Today.getFullYear(), 0, 1)) / (7 * 24 * 60 * 60 * 1000))}, (_, index) => index + 1).map(x=>[x,`week ${x}`]);
            }),
        onMounted(() => {
            this.renderTileValues();
            this.onChangerRenderSubcontract();
            this.onChangeRenderInternal();
            this.renderTeamTaskChart();
            this.renderCustomerCategoryChart();
            this.renderLeadStatusChart();
        })
    }

    // Method to open tree view for general models
    openTreeView(model, displayName, domain = []) {
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: displayName,
            res_model: model,
            view_mode: 'tree,form',
            views: [[false, 'tree'], [false, 'form']],
            domain: domain,
            target: 'current',
        });
    }

    // Method to open subcontract tree view based on filter selection
    openSubcontractTreeView(state) {
        const filterValue = this.subcontractFilter.el.value;
        let model, displayName, domain;

        if (filterValue === 'installation') {
            model = 'subcontract.installation.team.task';
            displayName = `Installation Tasks`;
            domain = [['installation_stage', '=', state]];
        } else if (filterValue === 'quality_assurance') {
            model = 'subcontract.quality.assurance.team.task';
            displayName = `QA Tasks`;
            domain = [['qa_stage', '=', state]];
        } else {
            // If no filter selected, show a notification or return
            this.env.services.notification.add("Please select a task type first.", {
                type: "warning",
            });
            return;
        }

        this.action.doAction({
            type: 'ir.actions.act_window',
            name: displayName,
            res_model: model,
            view_mode: 'tree,form',
            views: [[false, 'tree'], [false, 'form']],
            domain: domain,
            target: 'current',
        });
    }

    // Method to open internal team tree view based on filter selection
    openInternalTreeView(state) {
        const filterValue = this.internalFilter.el.value;
        let model, displayName, domain;

        if (filterValue === 'installation') {
            model = 'installation.team.task';
            displayName = `Internal Installation Tasks`;
            domain = [['installation_stage', '=', state]];
        } else if (filterValue === 'quality_assurance') {
            model = 'quality.assurance.team.task';
            displayName = `Internal QA Tasks`;
            domain = [['qa_stage', '=', state]];
        } else {
            // If no filter selected, show a notification or return
            this.env.services.notification.add("Please select a task type first.", {
                type: "warning",
            });
            return;
        }

        this.action.doAction({
            type: 'ir.actions.act_window',
            name: displayName,
            res_model: model,
            view_mode: 'tree,form',
            views: [[false, 'tree'], [false, 'form']],
            domain: domain,
            target: 'current',
        });
    }
    //method to render lead status chart to the view
    async renderLeadStatusChart(){
        var filter_cond=this.props.currentFilter??[];
        var leadStatusData = await this.orm.searchRead("crm.lead",[['type', '=', 'opportunity'],...filter_cond],["name","id","stage_id"])
        var leadStatusNew = leadStatusData.filter(x=>x.stage_id[0]==1)
        var leadStatusQualified = leadStatusData.filter(x=>x.stage_id[0]==2)
        var leadStatusProposition = leadStatusData.filter(x=>x.stage_id[0]==3)
        var leadStatusWon = leadStatusData.filter(x=>x.stage_id[0]==4)
        var ctx3 = this.ctx3.el.getContext('2d');
        this.myChart3 = new Chart(ctx3, {
            type: 'bar',
            data: {
                labels: ['New','Qualified','Proposition','Won'],
                datasets: [{
                    label: '',
                    data: [leadStatusNew.length,leadStatusQualified.length,leadStatusProposition.length,leadStatusWon.length],
                    backgroundColor: [
                        '#2CA1ED',
                        '#BE5458',
                        '#FFC222',
                        '#00DA93',

                    ],
                }]
            },
            options: {
                plugins: {
                    legend: {
                        display: false
                    },
                    title: {
                        display: false
                    }
                },
                scales: {
                      x: {
                        grid: {
                          display: false
                        }
                      },
                      y: {
                        grid: {
                          display: false
                        }
                      }
                    }
            }
        });
        this.currentLeadStatusChart=this.myChart3;
    }
//    method to render team task chart
    async renderTeamTaskChart(){
        var filter_cond=this.props.currentFilter??[];
        var installationTaskData = await this.orm.searchRead("installation.team.task",[['installation_stage','in',['new','in_progress']],...filter_cond], ["name","id","installation_stage"])
        var surveyTaskData = await this.orm.searchRead("site.inspection",[['inspection_state','in',['new','in_progress']]], ["name","id","inspection_state"])
        var qaTaskData = await this.orm.searchRead("quality.assurance.team.task",[['qa_stage','in',['new','in_progress']]],["name","id","qa_stage"])
        var ctx1 = this.ctx1.el.getContext('2d');
        this.myChart1 = new Chart(ctx1, {
            type: 'bar',
            data: {
                labels: ['Survey Team', 'Installation Team', 'QA Team'],
                datasets: [{
                    label: '',
                    data: [surveyTaskData.length, installationTaskData.length, qaTaskData.length],
                    backgroundColor: [
                        '#2CA1ED',
                        '#00DA93',
                        '#FFC222'
                    ],
                }]
            },
            options: {
                plugins: {
                    legend: {
                        display: false
                    },
                    title: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
        this.currentTeamTaskChart=this.myChart1;
    }
//method to render customer category chart
    async renderCustomerCategoryChart(){
        var filter_cond=this.props.currentFilter??[];
        var customerCategoryData = await this.orm.searchRead("customer.category",[], ["name","id"])
        var RenOrderData = await this.orm.searchRead("ren.order",[...filter_cond], ["customer_category_id","name","id"])
        var customerCategoryCountData=customerCategoryData.map(x=>RenOrderData.reduce((acc,y)=>y.customer_category_id[0]==x.id?acc+1:acc,0))
        var ctx2 = this.ctx2.el.getContext('2d');
        this.myChart2 = new Chart(ctx2, {
            type: 'doughnut',
            data: {
                labels: customerCategoryData.map(x=>x.name),
                datasets: [{
                    label: 'Customer Category',
                    data: customerCategoryCountData,
                }]
            },
            options: {
            }
        });
        this.currentCustomerCategoryChart=this.myChart2;
    }
//method to render subcontractor and internal team tiles
    async onChangeRenderInternal(){
        if (this.internalFilter.el.value=='installation'){
            this.internalNewCount.el.textContent=this.data['internal_installation_new_count']
            this.internalInProgressCount.el.textContent=this.data['internal_installation_in_progress_count']
            this.internalCompletedCount.el.textContent=this.data['internal_installation_completed_count']
            this.internalCancelledCount.el.textContent=this.data['internal_installation_cancelled_count']
        }
        else{
            this.internalNewCount.el.textContent=this.data['internal_qa_new_count']
            this.internalInProgressCount.el.textContent=this.data['internal_qa_in_progress_count']
            this.internalCompletedCount.el.textContent=this.data['internal_qa_completed_count']
            this.internalCancelledCount.el.textContent=this.data['internal_qa_cancelled_count']
        }
    }
//method to render tile values
    async renderTileValues(){
        this.renOrderCount.el.textContent=this.data['ren_order_count']
        this.materialOrderCount.el.textContent=this.data['material_order_count']
        this.materialArrivedCount.el.textContent=this.data['material_arrived_count']
        this.maintenanceRequestCount.el.textContent=this.data['maintenance_request_count']
        this.saleOrderCount.el.textContent=this.data['sale_order_count']
        this.orderCompletedCount.el.textContent=this.data['order_completed_count']
        this.inspectionNewCount.el.textContent=this.data['inspection_new_count']
        this.inspectionInProgressCount.el.textContent=this.data['inspection_in_progress_count']
        this.inspectionCompletedCount.el.textContent=this.data['inspection_completed_count']
        this.inspectionCancelledCount.el.textContent=this.data['inspection_cancelled_count']
    }
//method to render subcontractor tiles
    async onChangerRenderSubcontract(){
        if (this.subcontractFilter.el.value=='installation'){
            this.contractNewCount.el.textContent=this.data['contract_installation_new_count']
            this.contractInProgressCount.el.textContent=this.data['contract_installation_in_progress_count']
            this.contractCompletedCount.el.textContent=this.data['contract_installation_completed_count']
            this.contractCancelledCount.el.textContent=this.data['contract_installation_cancelled_count']
        }
        else{
            this.contractNewCount.el.textContent=this.data['contract_qa_new_count']
            this.contractInProgressCount.el.textContent=this.data['contract_qa_in_progress_count']
            this.contractCompletedCount.el.textContent=this.data['contract_qa_completed_count']
            this.contractCancelledCount.el.textContent=this.data['contract_qa_cancelled_count']
        }
    }
}
RenewableEnergyDashboard.template = "solar_renewable_energy.RenewableEnergyDashboard";
actionRegistry.add("renewable_energy_dashboard_tag", RenewableEnergyDashboard);