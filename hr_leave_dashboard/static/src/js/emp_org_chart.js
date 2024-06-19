/** @odoo-module */
import { useService } from "@web/core/utils/hooks";
import { usePopover } from "@web/core/popover/popover_hook";
import { onEmployeeSubRedirect } from "@hr_org_chart/fields/hooks"
const { Component, onWillStart, onWillRender, useState } = owl;
//The useUniquePopover function is a custom hook that enhances the functionality
//of a popover by ensuring that only one popover is visible at a time.
//It utilizes another hook called usePopover to manage the
//popover's state and behavior.
function useUniquePopover() {
    const popover = usePopover();
    let remove = null;
    return Object.assign(Object.create(popover), {
        add(target, component, props, options) {
            if (remove) {
                remove();
            }
            remove = popover.add(target, component, props, options);
            return () => {
                remove();
                remove = null;
            };
        },
    });
}
//Class TimeOffEmpOrgChartPopover that extends
//the Component class. It is a custom component used for handling
//popovers in an employee organization chart.
class TimeOffEmpOrgChartPopover extends Component {
    async setup() {
        super.setup();
        this.rpc = useService('rpc');
        this.orm = useService('orm');
        this.actionService = useService("action");
    }
    /**
     * Redirect to the employee form view.
     *
     * @private
     * @param {MouseEvent} event
     * @returns {Promise} action loaded
     */
    async _onEmployeeRedirect(employeeId) {
        const action = await this.orm.call('hr.employee', 'get_formview_action', [employeeId]);
        this.actionService.doAction(action);
    }
}
TimeOffEmpOrgChartPopover.template = 'hr_leave_dashboard.hr_orgchart_emp_popover';
//Exports a class TimeOffEmpOrgChart that extends the Component class.
//It is a custom component used for displaying an employee organization chart.
export class TimeOffEmpOrgChart extends Component {
    async setup() {
        super.setup();
        this.rpc = useService('rpc');
        this.orm = useService('orm');
        this.actionService = useService("action");
        this.popover = useUniquePopover();
        this.jsonStringify = JSON.stringify;
        this.state = useState({'employee_id': null});
        this._onEmployeeSubRedirect = onEmployeeSubRedirect();
        onWillStart(this.handleComponentUpdate.bind(this));
        onWillRender(this.handleComponentUpdate.bind(this));
    }
    /**
     * Called on start and on render
     */
    async handleComponentUpdate() {
        this.employee = this.props.id;
        // The widget is either displayed in the context of a hr.employee form or a res.users form
        this.state.employee_id = this.props;
        const forceReload = this.lastRecord !== this.props.record;
        this.lastRecord = this.props.record;
        await this.fetchEmployeeData(this.state.employee_id, forceReload);
    }
    async fetchEmployeeData(employeeId, force = false) {
    employeeId = this.props.id
        if (!employeeId) {
            this.managers = [];
            this.children = [];
            if (this.view_employee_id) {
                this.render(true);
            }
            this.view_employee_id = null;
        } else if (employeeId !== this.view_employee_id || force) {
            this.view_employee_id = employeeId;
            var orgData = await this.rpc(
                '/hr/get_org_chart',
                {
                    employee_id: employeeId,
                    context: Component.env.session.user_context,
                }
            );
            if (Object.keys(orgData).length === 0) {
                orgData = {
                    managers: [],
                    children: [],
                }
            }
            this.managers = orgData.managers;
            this.children = orgData.children;
            this.managers_more = orgData.managers_more;
            this.self = orgData.self;
            this.render(true);
        }
    }
    _onOpenPopover(event, employee) {
        this.popover.add(
            event.currentTarget,
            this.constructor.components.Popover,
            {employee},
            {closeOnClickAway: true}
        );
    }
    /**
     * Redirect to the employee form view.
     *
     * @private
     * @param {MouseEvent} event
     * @returns {Promise} action loaded
     */
    async _onEmployeeRedirect(employeeId) {
        const action = await this.orm.call('hr.employee', 'get_formview_action', [employeeId]);
        this.actionService.doAction(action);
    }
    async _onEmployeeMoreManager(managerId) {
        await this.fetchEmployeeData(managerId);
        this.state.employee_id = managerId;
    }
}
TimeOffEmpOrgChart.components = {
    Popover: TimeOffEmpOrgChartPopover,
};
TimeOffEmpOrgChart.template = 'hr_leave_dashboard.hr_org_chart';
