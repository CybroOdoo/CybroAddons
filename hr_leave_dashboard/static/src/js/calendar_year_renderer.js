/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { TimeOffCalendarYearRenderer } from "@hr_holidays/views/calendar/year/calendar_year_renderer";
import { usePublicHolidays } from "@hr_leave_dashboard/js/hooks";

patch(TimeOffCalendarYearRenderer.prototype, {
    setup() {
        super.setup();
        this.publicHolidays = usePublicHolidays(this.props);
    },
    onDayRender(info) {
        super.onDayRender(info);
        this.publicHolidays(info);
    }
});
