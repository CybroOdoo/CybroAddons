import { useService } from "@web/core/utils/hooks";
import { usePopover } from "@web/core/popover/popover_hook";
import { onEmployeeSubRedirect } from "@hr/fields/hooks";
import { Component, onWillStart, onWillRender, proxy, t, useProps } from "@odoo/owl";
import { session } from "@web/session";
import { rpc } from "@web/core/network/rpc";


class TimeOffEmpOrgChartPopover extends Component {
    static template = "hr_leave_dashboard.hr_orgchart_emp_popover";
    // The popover service passes the opened props plus a `close` callback.
    props = useProps({
        employee: t.any(),
        close: t.any().optional(),
    });

    setup() {
        super.setup();
        this.rpc = rpc;
        this.orm = useService("orm");
        this.actionService = useService("action");
        // Opens the direct / indirect / total subordinates list, as in core hr.
        this._onEmployeeSubRedirect = onEmployeeSubRedirect();
    }

    /**
     * Redirect to the employee default view.
     *
     * @private
     * @param {Number} employeeId
     */
    async _onEmployeeRedirect(employeeId) {
        const action = await this.orm.call("hr.employee", "get_record_default_action", [employeeId]);
        this.actionService.doAction(action);
    }
}

export class TimeOffEmpOrgChart extends Component {
    static template = "hr_leave_dashboard.hr_org_chart";
    static components = {
        Popover: TimeOffEmpOrgChartPopover,
    };
    props = useProps({
        name: t.any().optional(),
        id: t.any().optional(),
        job_id: t.any().optional(),
        manager: t.any().optional(),
        manager_all_count: t.any().optional(),
        child_all_count: t.any().optional(),
        record: t.any().optional(),
    });

    setup() {
        super.setup();

        this.rpc = rpc;
        this.orm = useService("orm");
        this.popover = usePopover(TimeOffEmpOrgChartPopover);
        this.actionService = useService("action");
        this.jsonStringify = JSON.stringify;
        this.state = proxy({
            employee_id: null,
            managers: [],
            children: [],
            managers_more: false,
            self: null,
        });
        this._view_employee_id = null;
        this._onEmployeeSubRedirect = onEmployeeSubRedirect();

        onWillStart(this.handleComponentUpdate.bind(this));
        onWillRender(this.handleComponentUpdate.bind(this));
    }

    get view_employee_id() {
        return this._view_employee_id;
    }

    get managers() {
        return this.state.managers;
    }

    get children() {
        return this.state.children;
    }

    get managers_more() {
        return this.state.managers_more;
    }

    get self() {
        return this.state.self;
    }

    async handleComponentUpdate() {
        this.employee = this.props.id;
        this.state.employee_id = this.props.id;
        const forceReload = this.lastRecord !== this.props.record;
        this.lastRecord = this.props.record;
        await this.fetchEmployeeData(this.state.employee_id, forceReload);
    }

    async fetchEmployeeData(employeeId, force = false) {
        employeeId = employeeId || this.props.id;
        if (!employeeId) {
            this.state.managers = [];
            this.state.children = [];
            this.state.managers_more = false;
            this.state.self = null;
            this._view_employee_id = null;
        } else if (employeeId !== this._view_employee_id || force) {
            this._view_employee_id = employeeId;
            let orgData = await this.rpc("/hr/get_org_chart", {
                employee_id: employeeId,
                context: {
                    ...(session.user_context || {}),
                    max_level: 3,
                },
            });

            if (!orgData || Object.keys(orgData).length === 0) {
                orgData = {
                    managers: [],
                    children: [],
                    managers_more: false,
                    self: null,
                };
            }

            this.state.managers = orgData.managers || [];
            this.state.children = orgData.children || [];
            this.state.managers_more = Boolean(orgData.managers_more);
            this.state.self = orgData.self || null;
        }
    }

    _onOpenPopover(event, employee) {
        this.popover.open(event.currentTarget, { employee });
    }

    async _onEmployeeRedirect(employeeId) {
        const action = await this.orm.call("hr.employee", "get_record_default_action", [employeeId]);
        this.actionService.doAction(action);
    }

    async _onEmployeeMoreManager(managerId) {
        await this.fetchEmployeeData(managerId, true);
        this.state.employee_id = managerId;
    }
}