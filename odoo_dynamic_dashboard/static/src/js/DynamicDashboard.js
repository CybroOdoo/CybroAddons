/** @odoo-module */

import { registry} from '@web/core/registry';
import { DynamicDashboardTile} from './DynamicDashboardTile'
import { DynamicDashboardChart} from './DynamicDashboardChart'
import { useService } from "@web/core/utils/hooks";
const { Component, mount} = owl
export class DynamicDashboard extends Component {
    setup(){
        this.action = useService("action");
        this.rpc = this.env.services.rpc
        this.renderDashboard()
    }
    async renderDashboard() {
        const action = this.action
        const rpc = this.rpc
        await this.rpc('/get/values', {'action_id': this.props.actionId}).then(function(response){
            if ($('.o_dynamic_dashboard')[0]){
                for (let i = 0; i < response.length; i++) {
                    if (response[i].type === 'tile'){
                        mount(DynamicDashboardTile, $('.o_dynamic_tile')[0], { props: {
                            widget: response[i], doAction: action
                        }});
                    }
                    else{
                        mount(DynamicDashboardChart, $('.o_dynamic_graph')[0], { props: {
                            widget: response[i], doAction: action, rpc: rpc
                        }});
                    }
                }
            }
        })
    }
    async _onClick_add_block(e){
        var self = this;
        var self_props = this.props;
        var self_env = self.env;
        var type = $(e.target).attr('data-type');
        await this.rpc('/create/tile',{'type' : type, 'action_id': self.props.actionId}).then(function(response){
                if(response['type'] == 'tile'){
                    mount(DynamicDashboardTile, $('.o_dynamic_tile')[0], { props: {
                        widget: response, doAction: self.action
                        }});
                    }
                else{
                    mount(DynamicDashboardChart, $('.o_dynamic_graph')[0], { props: {
                          widget: response, doAction: self.action
                          }});
                }
            })
    }
}
DynamicDashboard.template = "owl.dynamic_dashboard"
registry.category("actions").add("owl.dynamic_dashboard", DynamicDashboard)
