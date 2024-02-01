/** @odoo-module */
import { TimeOffCalendarModel } from '@hr_holidays/views/calendar/calendar_model';
import { serializeDate } from "@web/core/l10n/dates";
import { patch } from "@web/core/utils/patch";
//The patch function to modify the TimeOffCalendarModel prototype by adding or
//modifying several methods and properties: setup, updateData,
//fetchPublicHolidays, and a getter for publicHolidays.
patch(TimeOffCalendarModel.prototype, 'hr_holidays.TimeOffCalendarModel',{
    setup(params, services) {
        this._super(params, services);
        this.data.publicHolidays = {};
        if (this.env.isSmall) {
            this.meta.scale = 'month';
        }
    },
    async updateData(data) {
        await this._super(data);
        data.publicHolidays = await this.fetchPublicHolidays(data);
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
    }
});
