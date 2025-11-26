/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Component } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { onWillStart, onWillUpdateProps, useState } from "@odoo/owl";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { _t } from "@web/core/l10n/translation";
export class OrgChart extends Component {
    static template = "hierarchical_chart_widget.CustomerChartWidget";
    static props = { ...standardFieldProps };
    setup() {
        super.setup();
        this.orm = useService('orm');
        this.OrgState = useState({
            data: {},
        });
        onWillStart(async () => {
            const model = this.props.record.resModel;
            await this.DepartmentDetails(this.props.record.evalContextWithVirtualIds.id, model);
        });
        onWillUpdateProps(async (nextProps) => {
            const model = nextProps.record.resModel;
            await this.DepartmentDetails(nextProps.record.evalContextWithVirtualIds.id, model);
        });

    }
    async DepartmentDetails(department_id, model) {
        // Fetching the details for the template
        this.OrgState.data = await this.orm.call(
            'hr.department',
            'get_child_dept',
            [department_id, model]
        );
    }
    onChildClick(id, ev) {
        // On clicking the nodes it will be redirected to their page
        const action = {
            type: 'ir.actions.act_window',
            res_model: ev.props.record.resModel,
            res_id: id,
            domain: [],
            views: [
                [false, "form"],
                [false, "list"],
            ],
            name: "Schedule Log",
            target: 'current',
        };
        ev.env.services.action.doAction(action);
    }
}
export const orgChart = {
    component: OrgChart,
    displayName: _t("Widget"),
    supportedTypes: ["many2one"],
    extractProps: ({ attrs }) => ({}),
};
registry.category("fields").add("org_chart", orgChart);
