/** @odoo-module **/
import { registry } from "@web/core/registry";
const { Component,onWillStart,useState,onWillUpdateProps} = owl;
import { useService } from "@web/core/utils/hooks";
export class OrgChart extends Component {
    static template = 'CustomerChartWidget'
    setup(){
        super.setup();
        this.orm = useService('orm')
        var self = this
        this.OrgState = useState({
            data: {},
        });
        onWillStart( async() => {
            console.log(this.props.record.resModel)
            var model = this.props.record.resModel
            await this.DepartmentDetails(this.props.record.data.id,model)
        })
        onWillUpdateProps(async (nextProps) => {
            var model = this.props.record.resModel
            await this.DepartmentDetails(nextProps.record.data.id,model);
        });
    }
    async DepartmentDetails(department_id,model){
        //----fetching the details for template
        var self=this
             self.OrgState.data = await this.orm.call(
                'hr.department',
                'get_child_dept',
                [department_id,model]
            )
    }
    onChildClick(id,ev){
        //----on clicking the nodes it will be redirected to their page
        const action = {
                type: 'ir.actions.act_window',
                res_model:ev.props.record.resModel,
                res_id:id,
                domain: [],
                views: [ [false, "form"],[false, "list"],],
                name: "Schedule Log",
                target: 'current',
            };
        ev.env.services.action.doAction(action)
    }
}
registry.category("fields").add("org_chart", OrgChart);