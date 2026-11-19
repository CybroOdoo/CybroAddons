import { patch } from "@web/core/utils/patch";
import { TimeOffCalendarYearRenderer } from "@hr_holidays/views/calendar/year/calendar_year_renderer";
import { usePublicHolidays } from "./hooks";

patch(TimeOffCalendarYearRenderer.prototype, {
    setup() {
        super.setup();
        this.publicHolidays = usePublicHolidays(this.props);
    },

    getDayCellClassNames(info) {
        return [...super.getDayCellClassNames(info), ...this.publicHolidays(info)];
    },
});
