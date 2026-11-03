/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Component, onWillStart, onWillUpdateProps, proxy, useProps } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { _t } from "@web/core/l10n/translation";

export class OrgChart extends Component {
    static template = "hierarchical_chart_widget.CustomerChartWidget";
    props = useProps(standardFieldProps);

    setup() {
        super.setup();
        this.orm = useService("orm");
        this.action = useService("action");
        this.OrgState = proxy({
            data: {
                parent: null,
                self: false,
                child: [],
            },
        });
        onWillStart(async () => {
            const model = this.props.record.resModel;
            const resId = this.props.record.resId || this.props.record.evalContextWithVirtualIds?.id;
            await this.DepartmentDetails(resId, model);
        });
        onWillUpdateProps(async (nextProps) => {
            const model = nextProps.record.resModel;
            const resId = nextProps.record.resId || nextProps.record.evalContextWithVirtualIds?.id;
            await this.DepartmentDetails(resId, model);
        });
    }

    async DepartmentDetails(department_id, model) {
        if (!department_id) {
            this.OrgState.data = {
                parent: null,
                self: false,
                child: [],
            };
            return;
        }
        // Fetch the details for the template
        const data = await this.orm.call(
            model || 'hr.department',
            'get_child_dept',
            [department_id]
        );
        this.OrgState.data = data || {
            parent: null,
            self: false,
            child: [],
        };
    }

    onChildClick(id) {
        if (!id) return;
        // Redirect to the department record when a node is clicked
        const action = {
            type: 'ir.actions.act_window',
            res_model: this.props.record.resModel || 'hr.department',
            res_id: id,
            domain: [],
            views: [
                [false, "form"],
                [false, "list"],
            ],
            name: "Department",
            target: 'current',
        };
        this.action.doAction(action);
    }
}

export const orgChart = {
    component: OrgChart,
    displayName: _t("Widget"),
    supportedTypes: ["many2one", "one2many"],
    extractProps: () => ({}),
};
registry.category("fields").add("org_chart", orgChart);
