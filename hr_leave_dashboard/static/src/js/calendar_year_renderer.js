/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { TimeOffCalendarYearRenderer } from "@hr_holidays/views/calendar/year/calendar_year_renderer";
import { usePublicHolidays } from '@hr_leave_dashboard/js/hooks';
//The patch function to modify the TimeOffCalendarYearRenderer prototype
//by adding or modifying two methods: setup and onDayRender.
patch(TimeOffCalendarYearRenderer.prototype, 'hr_leave_dashboard.TimeOffCalendarYearRenderer',{
    setup() {
        this._super(...arguments);
        this.publicHolidays = usePublicHolidays(this.props);
    },
    onDayRender(info) {
        this._super(info);
        this.publicHolidays(info);
    }
});
