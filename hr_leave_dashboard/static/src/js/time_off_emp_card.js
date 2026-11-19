import { useService } from "@web/core/utils/hooks";
import { user } from "@web/core/user";
import { Component, onWillStart, proxy, t, useProps } from "@odoo/owl";

export class TimeOffEmpCard extends Component {
    static template = "hr_leave_dashboard.TimeOffEmpCard";
    props = useProps({
        name: t.any().optional(),
        id: t.any().optional(),
        department_id: t.any().optional(),
        job_position: t.any().optional(),
        children: t.any().optional(),
        image_1920: t.any().optional(),
        work_email: t.any().optional(),
        work_phone: t.any().optional(),
        company: t.any().optional(),
        resource_calendar_id: t.any().optional(),
    });
}

export class EmpDepartmentCard extends Component {
    static template = "hr_leave_dashboard.EmpDepartmentCard";
    props = useProps({
        name: t.any().optional(),
        id: t.any().optional(),
        department_id: t.any().optional(),
        child_all_count: t.any().optional(),
        children: t.any().optional(),
        absentees: t.any().optional(),
        current_shift: t.any().optional(),
        upcoming_holidays: t.any().optional(),
    });

    /**
     * Split an ISO date (YYYY-MM-DD) into the parts shown on the holiday
     * "calendar leaf": short month, day number and weekday.
     */
    dateParts(isoDate) {
        const date = isoDate && luxon.DateTime.fromISO(isoDate);
        if (!date || !date.isValid) {
            return { month: "", day: "-", weekday: "" };
        }
        return {
            month: date.toFormat("LLL"),
            day: date.toFormat("d"),
            weekday: date.toFormat("ccc, yyyy"),
        };
    }

    /** Number of days a holiday spans, or 0 for a single-day holiday. */
    spanDays(holiday) {
        if (!holiday.date_from || !holiday.date_to) {
            return 0;
        }
        const from = luxon.DateTime.fromISO(holiday.date_from);
        const to = luxon.DateTime.fromISO(holiday.date_to);
        const days = Math.round(to.diff(from, "days").days) + 1;
        return days > 1 ? days : 0;
    }
}

export class ApprovalStatusCard extends Component {
    static template = "hr_leave_dashboard.ApprovalStatusCard";
    props = useProps({
        id: t.any().optional(),
        name: t.any().optional(),
        approval_status_count: t.any().optional(),
        child_ids: t.any().optional(),
        children: t.any().optional(),
        all_validated_leaves: t.any().optional(),
    });

    setup() {
        super.setup();
        this.userService = user;
        this.state = proxy({
            select: "today",
            // employee id -> counts for the selected period
            counts: {},
        });
        this.manager = false;
        this.actionService = useService("action");
        this.orm = useService("orm");

        onWillStart(async () => {
            this.manager = await this.userService.hasGroup("hr_holidays.group_hr_holidays_manager");
            if (this.manager) {
                await this.loadTeamCounts();
            }
        });
    }

    /** Counts shown in the My Team table for one employee. */
    countsFor(child) {
        return this.state.counts[child.id] || {};
    }

    async loadTeamCounts() {
        const ids = (this.props.children || []).map((child) => child.id);
        if (!ids.length) {
            this.state.counts = {};
            return;
        }
        this.state.counts = await this.orm.call(
            "hr.leave",
            "get_team_approval_status_counts",
            [ids, this.state.select]
        );
    }

    async onPeriodChange(period) {
        this.state.select = period;
        await this.loadTeamCounts();
    }

    async printPdfReport() {
        const duration = this.state.select;
        return this.actionService.doAction({
            type: "ir.actions.report",
            report_type: "qweb-pdf",
            report_name: "hr_leave_dashboard.hr_leave_report",
            data: {
                duration: duration,
                all_validated_leaves: this.props.all_validated_leaves,
            },
        });
    }
}
