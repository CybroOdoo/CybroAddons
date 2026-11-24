import { _t } from "@web/core/l10n/translation";

/* Helpers shared by the AeroCourt interactions: dates, money, escaping and the
   booking setup chosen in the Website settings. */

export const pad = (n) => String(n).padStart(2, "0");

export const toISODate = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;

export const fromISODate = (s) => {
    const [y, m, d] = s.split("-").map(Number);
    return new Date(y, m - 1, d);
};

export const startOfToday = () => {
    const d = new Date();
    d.setHours(0, 0, 0, 0);
    return d;
};

export const addDays = (date, n) => {
    const d = new Date(date);
    d.setDate(d.getDate() + n);
    return d;
};

/** English readers keep the day-first format of the design. */
const locale = () => {
    const lang = document.documentElement.lang || "en-GB";
    return lang.startsWith("en") ? "en-GB" : lang;
};

export const formatDate = (d, opts = { weekday: "short", day: "numeric", month: "short" }) =>
    d.toLocaleDateString(locale(), opts);

export const longDate = (iso) =>
    formatDate(fromISODate(iso), { weekday: "long", day: "numeric", month: "long" });

export const escapeHTML = (s) =>
    String(s).replace(
        /[&<>"']/g,
        (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]
    );

export const prefersReducedMotion = () =>
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

const PERIOD_ICONS = {
    Morning: "ph-sun-bold",
    Afternoon: "ph-sun-bold",
    Evening: "ph-moon-stars-bold",
};

export const periodLabel = (period) =>
    ({ Morning: _t("Morning"), Afternoon: _t("Afternoon"), Evening: _t("Evening") })[period];

const periodOf = (hour) => (hour < 12 ? "Morning" : hour < 17 ? "Afternoon" : "Evening");
const hourLabel = (hour) => `${pad(hour % 12 || 12)}:00 ${hour < 12 ? "AM" : "PM"}`;

let config = null;

/**
 * The booking setup, read once from the `.ac-config` element which the layout
 * fills with the values of Website > Settings > AeroCourt Club.
 */
export function getConfig() {
    if (config) {
        return config;
    }
    const data = document.querySelector(".ac-config")?.dataset || {};
    const openHour = Number(data.openHour ?? 6);
    const closeHour = Number(data.closeHour ?? 23);
    const courtCount = Number(data.courts ?? 4);
    // Every court is identical: a free one is assigned by the server on booking
    const courts = Array.from({ length: courtCount }, (_, i) => ({
        id: `court-${pad(i + 1)}`,
        number: pad(i + 1),
    }));
    // One slot per opening hour
    const timeSlots = Array.from({ length: Math.max(closeHour - openHour, 0) }, (_, i) => {
        const hour = openHour + i;
        return { value: `${pad(hour)}:00`, label: hourLabel(hour), hour, period: periodOf(hour) };
    });
    const periods = ["Morning", "Afternoon", "Evening"]
        .map((period) => {
            const hours = timeSlots.filter((s) => s.period === period).map((s) => s.hour);
            return hours.length
                ? {
                      period,
                      icon: PERIOD_ICONS[period],
                      range: `${pad(hours[0])}:00 – ${pad(hours[hours.length - 1] + 1)}:00`,
                  }
                : null;
        })
        .filter(Boolean);
    config = {
        currency: data.currency || "$",
        openHour,
        closeHour,
        courtRate: Number(data.courtRate ?? 18),
        rentalFee: Number(data.rentalFee ?? 5),
        bookingWindowDays: Number(data.bookingDays ?? 30),
        courts,
        timeSlots,
        periods,
        slotsPerDay: courts.length * timeSlots.length,
    };
    return config;
}

/**
 * Text or number of a `data-ac` marker, taken from the club settings. The pages
 * hold plain sample text so the website builder can edit them.
 *
 * @param {string} key marker name
 * @return {string|number|null} null when the marker is unknown
 */
export function configValue(key) {
    const c = getConfig();
    const hours = `${pad(c.openHour)}:00 – ${pad(c.closeHour)}:00`;
    const values = {
        hours,
        "hours-short": `${pad(c.openHour)}–${pad(c.closeHour)}`,
        currency: c.currency,
        rate: String(c.courtRate),
        "booking-days": String(c.bookingWindowDays),
        courts: c.courts.length,
        "open-hours": c.closeHour - c.openHour,
    };
    return values[key] ?? null;
}

export const money = (n) =>
    n === 0 ? _t("Free") : `${getConfig().currency}${n.toLocaleString("en-US")}`;

/**
 * Next calendar date for a weekly session time such as "Thu 18:30".
 *
 * @param {string} label day and time, as written on the session card
 * @return {{date: string, start: string}|null} null when the label is not understood
 */
export function nextSessionDate(label) {
    const match = /^\s*(Sun|Mon|Tue|Wed|Thu|Fri|Sat)\w*\s+(\d{1,2}):(\d{2})/i.exec(label || "");
    if (!match) {
        return null;
    }
    const target = ["sun", "mon", "tue", "wed", "thu", "fri", "sat"].indexOf(match[1].toLowerCase());
    const [h, m] = [Number(match[2]), Number(match[3])];
    const now = new Date();
    const today = startOfToday();
    for (let i = 0; i < 8; i++) {
        const candidate = addDays(today, i);
        const at = new Date(candidate);
        at.setHours(h, m, 0, 0);
        if (candidate.getDay() === target && at > now) {
            return { date: toISODate(candidate), start: `${match[2]}:${match[3]}` };
        }
    }
    return { date: toISODate(addDays(today, 7)), start: `${match[2]}:${match[3]}` };
}
