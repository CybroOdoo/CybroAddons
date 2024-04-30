/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { TimeOffDashboard } from '@hr_holidays/dashboard/time_off_dashboard';
import { TimeOffCard } from '@hr_holidays/dashboard/time_off_card';
import { TimeOffEmpCard } from './time_off_emp_card';
import { TimeOffEmpOrgChart } from './emp_org_chart';
import { EmpDepartmentCard } from './time_off_emp_card';
import { ApprovalStatusCard } from './time_off_emp_card';
import { Component, onWillStart, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

//The code is a patch that modifies the loadDashboardData method of the TimeOffDashboard class.
patch(TimeOffDashboard.prototype,{

    setup() {
        super.setup();
         this.userService = useService('user');
        this.currentEmployee = useState({
            data: {}

        })
         this.currentAbsentees = useState({
            data: {}

        })
        this.currentShift = useState({
            data: {}

        })
        this.upcoming_holidays = useState({
            data: {}

        })

        onWillStart(async() => {
            await this.userService.hasGroup('hr_holidays.group_hr_holidays_manager').then(hasGroup => {
                this.manager = hasGroup;
            })
            this.currentEmployee.data = await this.orm.call(
            'hr.leave',
            'get_current_employee',
            [],
            {
                context: {
                    employee_id: this.props.employeeId
                }
            }
        );
         this.currentAbsentees.data = await this.orm.call(
            'hr.leave',
            'get_absentees',
            [],
            {
                 context: {
                    employee_id: this.props.employeeId
                }
            }

        );
         this.currentShift.data = await this.orm.call(
            'hr.leave',
            'get_current_shift',
            [],
            {
                context: {
                    employee_id: this.props.employeeId
                }
            }
        );
         this.upcoming_holidays.data = await this.orm.call(
            'hr.leave',
            'get_upcoming_holidays',
            [],
            {
                context: {
                    employee_id: this.props.employeeId
                }
            }
        );
         this.approval_status_count = await this.orm.call(
            'hr.leave',
            'get_approval_status_count',
            [this.currentEmployee.data.id],
            {
                context: {
                    employee_id: this.props.employeeId
                }
            }
        );
          this.all_validated_leaves = await this.orm.call(
            'hr.leave',
            'get_all_validated_leaves',
            [],
            {
                context: {
                    employee_id: this.props.employeeId
                }
            }
        );
        if (this.props.employeeId == null) {
            this.props.employeeId = this.currentEmployee.data.id;
        }

        })
    },
});
TimeOffDashboard.components = { ...TimeOffDashboard.components, TimeOffCard, TimeOffEmpCard ,TimeOffEmpOrgChart, EmpDepartmentCard, ApprovalStatusCard};
