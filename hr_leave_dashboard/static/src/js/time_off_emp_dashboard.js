import { patch } from "@web/core/utils/patch";
import { TimeOffDashboard } from "@hr_holidays/dashboard/time_off_dashboard";
import { user } from "@web/core/user";
import { TimeOffEmpCard, EmpDepartmentCard, ApprovalStatusCard } from "./time_off_emp_card";
import { TimeOffEmpOrgChart } from "./emp_org_chart";
import { onWillStart, proxy } from "@odoo/owl";

patch(TimeOffDashboard.prototype, {
    setup() {
        super.setup();
        this.userService = user;
        this.manager = false;
        this.currentEmployee = proxy({
            data: {},
        });
        this.currentAbsentees = proxy({
            data: [],
        });
        this.currentShift = proxy({
            data: false,
        });
        this.upcoming_holidays = proxy({
            data: [],
        });
        this.approval_status_count = proxy({
            validate_count: 0,
            confirm_count: 0,
            refuse_count: 0,
        });
        this.all_validated_leaves = [];

        onWillStart(async () => {
            this.manager = await this.userService.hasGroup("hr_holidays.group_hr_holidays_manager");
            const empContext = { employee_id: this.props.employeeId };

            const empData = await this.orm.call(
                "hr.leave",
                "get_current_employee",
                [],
                { context: empContext }
            );
            this.currentEmployee.data = empData || {};

            const absenteesData = await this.orm.call(
                "hr.leave",
                "get_absentees",
                [],
                { context: empContext }
            );
            this.currentAbsentees.data = absenteesData || [];

            const shiftData = await this.orm.call(
                "hr.leave",
                "get_current_shift",
                [],
                { context: empContext }
            );
            this.currentShift.data = shiftData || false;

            const upcomingData = await this.orm.call(
                "hr.leave",
                "get_upcoming_holidays",
                [],
                { context: empContext }
            );
            this.upcoming_holidays.data = upcomingData || [];

            const empId = this.currentEmployee.data?.id;
            if (empId) {
                const countData = await this.orm.call(
                    "hr.leave",
                    "get_approval_status_count",
                    [empId],
                    { context: empContext }
                );
                Object.assign(this.approval_status_count, countData || {});
            }

            this.all_validated_leaves = await this.orm.call(
                "hr.leave",
                "get_all_validated_leaves",
                [],
                { context: empContext }
            );
        });
    },
});

Object.assign(TimeOffDashboard.components, {
    TimeOffEmpCard,
    TimeOffEmpOrgChart,
    EmpDepartmentCard,
    ApprovalStatusCard,
});
