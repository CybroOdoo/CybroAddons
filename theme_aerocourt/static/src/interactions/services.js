/** Server calls and booking helpers used by the forms and the calendar. */

import { rpc } from "@web/core/network/rpc";
import { addDays, getConfig, startOfToday, toISODate } from "./utils";

/* Calls to the website routes of the theme (controllers/theme_aerocourt.py). */

export const bookingService = {
    taken: null,

    /** Courts already booked, for the whole booking window in one request. */
    load() {
        if (!this.taken) {
            const first = startOfToday();
            this.taken = rpc("/aerocourt/availability", {
                date_from: toISODate(first),
                date_to: toISODate(addDays(first, getConfig().bookingWindowDays)),
            }).catch(() => ({}));
        }
        return this.taken;
    },

    refresh() {
        this.taken = null;
    },

    /** Free and taken slots of one court on one day. */
    async getAvailability(courtId, isoDate) {
        const { courts, timeSlots } = getConfig();
        const court = courts.find((c) => c.id === courtId);
        const taken = (await this.load())[isoDate] || {};
        const now = new Date();
        const isToday = isoDate === toISODate(now);
        const slots = timeSlots.map((s) => {
            const booked = (taken[s.value] || []).includes(court.number);
            const past = isToday && s.hour <= now.getHours();
            return { ...s, available: !booked && !past, reason: past ? "Passed" : booked ? "Booked" : "" };
        });
        const openCount = slots.filter((s) => s.available).length;
        return { available: openCount > 0, openCount, slots };
    },

    /** Creates the CRM lead of a court booking; the server picks the court. */
    async createBooking(payload) {
        const res = await rpc("/aerocourt/request", { kind: "court", ...payload });
        this.refresh();
        if (res.error) {
            throw new Error(res.error);
        }
        return { ...payload, reference: res.reference, courtNumber: res.court };
    },
};

/** Creates the CRM lead of a session, membership or contact request. */
export async function register(kind, payload) {
    const res = await rpc("/aerocourt/request", { kind, ...payload });
    if (res.error) {
        throw new Error(res.error);
    }
    return { reference: res.reference, kind, ...payload };
}
