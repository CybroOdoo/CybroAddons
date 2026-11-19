import { TimeOffCalendarModel } from "@hr_holidays/views/calendar/calendar_model";
import { serializeDate } from "@web/core/l10n/dates";
import { patch } from "@web/core/utils/patch";

patch(TimeOffCalendarModel.prototype, {
    setup(params, services) {
        super.setup(params, services);
        this.data.publicHolidays = {};
        if (this.uiService.isSmall) {
            this.meta.scale = "month";
        }
    },

    async updateData(data) {
        const prom = super.updateData(data);
        data.publicHolidays = await this.fetchPublicHolidays(data);
        return prom;
    },

    // Fetches public holidays in a year
    async fetchPublicHolidays(data) {
        return this.orm.call("hr.employee", "get_public_holidays", [
            this.employeeId,
            serializeDate(data.range.start, "datetime"),
            serializeDate(data.range.end, "datetime"),
        ]);
    },

    get publicHolidays() {
        return this.data.publicHolidays;
    },
});
