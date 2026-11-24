/** Interactions of the court booking page: price summary and availability calendar. */

import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { AcInteraction } from "./base";
import { Interaction } from "@web/public/interaction";
import { fieldError, setLoading, validateForm } from "./forms";
import { getModal, getModalBody } from "./modal";
import { bookingService } from "./services";
import {
    addDays,
    escapeHTML,
    formatDate,
    fromISODate,
    getConfig,
    longDate,
    money,
    pad,
    periodLabel,
    prefersReducedMotion,
    startOfToday,
    toISODate,
} from "./utils";

const MAX_RENTALS = 4; // up to 4 players per court

const rentalText = (n) =>
    n ? (n > 1 ? _t("%s racket sets", n) : _t("%s racket set", n)) : _t("None");

const courtsText = (n) => (n === 1 ? _t("%s court free", n) : _t("%s courts free", n));

const slotRange = (slot) =>
    `${slot.label} – ${pad((slot.hour + 1) % 12 || 12)}:00 ${slot.hour + 1 >= 12 ? "PM" : "AM"}`;

/** The hourly rate shown next to the calendar, from the Website settings. */
export class AcBookingRate extends Interaction {
    static selector = "#bkRate";
    dynamicContent = {
        _root: { "t-out": () => money(getConfig().courtRate) },
    };
}

/**
 * Court booking: calendar of the booking window, then the modal steps
 * time & extras, details and confirmation. The booking becomes a CRM lead and
 * the free courts always come from the leads already taken.
 */
export class AcBookingCalendar extends AcInteraction {
    static selector = "#bookingCalendar";
    dynamicContent = {
        "#calMonth": {
            "t-out": () =>
                this.viewMonth.toLocaleDateString(document.documentElement.lang?.startsWith("en") ? "en-GB" : undefined, {
                    month: "long",
                    year: "numeric",
                }),
        },
        "#calPrev": {
            "t-on-click": () => this.shiftMonth(-1),
            "t-att-disabled": () => this.isFirstMonth(),
        },
        "#calNext": {
            "t-on-click": () => this.shiftMonth(1),
            "t-att-disabled": () => this.isLastMonth(),
        },
        "#calGrid": {
            "t-on-pointerover": this.onPointerOver,
            "t-on-pointerleave": this.hideTip,
            "t-on-focusin": this.onFocusIn,
            "t-on-focusout": this.hideTip,
            "t-on-click": this.onDayClick,
            "t-on-keydown": this.onDayKeyDown,
        },
        _window: { "t-on-scroll.noUpdate": this.hideTip },
    };

    setup() {
        this.config = getConfig();
        this.firstDay = startOfToday();
        this.lastDay = addDays(this.firstDay, this.config.bookingWindowDays);
        this.viewMonth = new Date(this.firstDay.getFullYear(), this.firstDay.getMonth(), 1);
        this.dayCache = new Map(); // ISO date -> aggregated availability
        this.draft = null; // the booking being built inside the modal
        this.grid = this.el.querySelector("#calGrid");
        this.tip = this.el.querySelector("#calTip");
    }

    async willStart() {
        await this.renderCalendar();
    }

    start() {
        // The steps of the booking live in the shared modal
        const body = getModalBody();
        this.addListener(body, "click", (ev) => this.onModalClick(ev));
        this.addListener(body, "change", (ev) => this.onModalChange(ev));
        this.addListener(body, "submit", (ev) => this.onModalSubmit(ev));
    }

    /* ---------- availability ---------- */
    async dayAvailability(iso) {
        if (this.dayCache.has(iso)) {
            return this.dayCache.get(iso);
        }
        const { courts, periods } = this.config;
        const results = await Promise.all(courts.map((c) => bookingService.getAvailability(c.id, iso)));
        const perCourt = Object.fromEntries(courts.map((c, i) => [c.id, results[i]]));
        const freeSlots = results.flatMap((r) => r.slots).filter((s) => s.available);
        const info = {
            iso,
            perCourt,
            free: freeSlots.length,
            byPeriod: Object.fromEntries(
                periods.map((p) => [p.period, freeSlots.filter((s) => s.period === p.period).length])
            ),
        };
        this.dayCache.set(iso, info);
        return info;
    }

    levelFor(free) {
        return free === 0 ? "full" : free / this.config.slotsPerDay >= 0.5 ? "plenty" : "limited";
    }

    courtsFreeAt(info, slotValue) {
        return this.config.courts.filter(
            (c) => info.perCourt[c.id].slots.find((s) => s.value === slotValue)?.available
        );
    }

    /* ---------- calendar ---------- */
    isFirstMonth() {
        return (
            this.viewMonth.getFullYear() === this.firstDay.getFullYear() &&
            this.viewMonth.getMonth() === this.firstDay.getMonth()
        );
    }

    isLastMonth() {
        return new Date(this.viewMonth.getFullYear(), this.viewMonth.getMonth() + 1, 1) > this.lastDay;
    }

    async shiftMonth(step) {
        this.viewMonth = new Date(this.viewMonth.getFullYear(), this.viewMonth.getMonth() + step, 1);
        this.hideTip();
        await this.waitFor(this.renderCalendar());
    }

    async renderCalendar() {
        const year = this.viewMonth.getFullYear();
        const month = this.viewMonth.getMonth();
        const offset = (new Date(year, month, 1).getDay() + 6) % 7; // Monday-first grid
        const daysInMonth = new Date(year, month + 1, 0).getDate();
        const days = Array.from({ length: daysInMonth }, (_, i) => new Date(year, month, i + 1));
        const bookable = days.filter((d) => d >= this.firstDay && d <= this.lastDay);
        const infos = new Map(
            (await Promise.all(bookable.map((d) => this.dayAvailability(toISODate(d))))).map((x) => [x.iso, x])
        );

        const cells = Array.from(
            { length: offset },
            () => '<span class="ac-cal-day ac-cal-day--blank" aria-hidden="true"></span>'
        );
        days.forEach((d) => {
            const iso = toISODate(d);
            const info = infos.get(iso);
            const isToday = iso === toISODate(this.firstDay);
            if (!info) {
                const past = d < this.firstDay;
                cells.push(`
                    <span class="ac-cal-day ${past ? "is-past" : "is-later"}" aria-disabled="true" title="${past ? _t("Past date") : _t("Opens for booking later")}">
                      <span class="ac-cal-day__num">${d.getDate()}</span>
                    </span>`);
                return;
            }
            const label = info.free ? _t("%s slots free", info.free) : _t("fully booked");
            cells.push(`
                <button type="button" class="ac-cal-day is-${this.levelFor(info.free)}${isToday ? " is-today" : ""}" data-date="${iso}"
                        style="--fill:${(info.free / this.config.slotsPerDay).toFixed(2)}"
                        aria-label="${longDate(iso)}, ${label}" ${info.free ? "" : 'aria-disabled="true"'}>
                  <span class="ac-cal-day__num">${d.getDate()}</span>
                  ${isToday ? `<span class="ac-cal-day__today">${_t("Today")}</span>` : ""}
                  <span class="ac-cal-day__meter" aria-hidden="true"><span></span></span>
                  <span class="ac-cal-day__free">${info.free ? `<b>${info.free}</b><span class="ac-cal-day__word"> ${_t("free")}</span>` : _t("Full")}</span>
                </button>`);
        });
        this.setHTML(this.grid, cells.join(""));
    }

    /* ---------- hover / focus preview ---------- */
    onPointerOver(ev) {
        if (ev.pointerType === "touch") {
            return;
        }
        const cell = ev.target.closest(".ac-cal-day[data-date]");
        if (cell) {
            this.showTip(cell);
        }
    }

    onFocusIn(ev) {
        const cell = ev.target.closest(".ac-cal-day[data-date]");
        if (cell && cell.matches(":focus-visible")) {
            this.showTip(cell);
        }
    }

    showTip(cell) {
        const tip = this.tip;
        const info = this.dayCache.get(cell.dataset.date);
        if (!info) {
            return;
        }
        tip.innerHTML = `
            <p class="ac-cal-tip__date">${longDate(info.iso)}</p>
            <p class="ac-cal-tip__total">${_t("%(free)s of %(total)s court slots free", {
                free: `<strong>${info.free}</strong>`,
                total: this.config.slotsPerDay,
            })}</p>
            <div class="ac-cal-tip__split">
              ${this.config.periods.map((p) => `<span><i class="ac-icon ac-i-${p.icon}" aria-hidden="true"></i> ${periodLabel(p.period)} <b>${info.byPeriod[p.period]}</b></span>`).join("")}
            </div>
            <p class="ac-cal-tip__cta">${info.free ? _t("Click to choose a time") : _t("No courts left on this day")}</p>`;
        tip.hidden = false;

        // Position above the cell (or below if there is no room), clamped to the card
        const card = this.el.getBoundingClientRect();
        const r = cell.getBoundingClientRect();
        const tw = tip.offsetWidth;
        const th = tip.offsetHeight;
        let left = r.left - card.left + r.width / 2 - tw / 2;
        left = Math.max(12, Math.min(left, card.width - tw - 12));
        let top = r.top - card.top - th - 10;
        tip.classList.toggle("is-below", top < 8);
        if (top < 8) {
            top = r.bottom - card.top + 10;
        }
        tip.style.setProperty("--x", `${left}px`);
        tip.style.setProperty("--y", `${top}px`);
        this.waitForAnimationFrame(() => tip.classList.add("is-visible"));
    }

    hideTip() {
        this.tip.classList.remove("is-visible");
        this.tip.hidden = true;
    }

    onDayClick(ev) {
        const cell = ev.target.closest(".ac-cal-day[data-date]");
        if (!cell || cell.getAttribute("aria-disabled") === "true") {
            return;
        }
        this.hideTip();
        return this.openTimes(cell.dataset.date);
    }

    /** Arrow keys move between the days. */
    onDayKeyDown(ev) {
        const cell = ev.target.closest(".ac-cal-day[data-date]");
        const moves = { ArrowLeft: -1, ArrowRight: 1, ArrowUp: -7, ArrowDown: 7 };
        if (!cell || !(ev.key in moves)) {
            return;
        }
        ev.preventDefault();
        const target = toISODate(addDays(fromISODate(cell.dataset.date), moves[ev.key]));
        this.grid.querySelector(`.ac-cal-day[data-date="${target}"]`)?.focus();
    }

    /* ---------- draft of the booking ---------- */
    get court() {
        return this.config.courts.find((c) => c.id === this.draft.courtId);
    }

    get slot() {
        return this.config.timeSlots.find((s) => s.value === this.draft.slot);
    }

    get rentals() {
        return this.draft.rental ? this.draft.rentalCount : 0;
    }

    get total() {
        return this.draft.slot ? this.config.courtRate + this.rentals * this.config.rentalFee : 0;
    }

    /* ---------- modal: step progress ---------- */
    flowSteps(current) {
        return `
            <ol class="ac-bk-flow__steps" aria-label="${_t("Booking progress, step %(step)s of 2", { step: current + 1 })}">
              ${[_t("Time & extras"), _t("Your details")]
                  .map(
                      (label, i) => `
                <li class="${i < current ? "is-done" : i === current ? "is-current" : ""}" ${i === current ? 'aria-current="step"' : ""}>
                  <span>${i < current ? '<i class="ac-icon ac-i-ph-check-bold" aria-hidden="true"></i>' : i + 1}</span><em>${label}</em>
                </li>`
                  )
                  .join("")}
            </ol>`;
    }

    /* ---------- modal view 1: time & extras ---------- */
    timesHTML(info) {
        const { courts, timeSlots, periods } = this.config;
        return periods
            .map(
                ({ period, icon, range }) => `
            <div class="ac-bk-times__group">
              <p class="ac-bk-times__label"><i class="ac-icon ac-i-${icon}" aria-hidden="true"></i> ${periodLabel(period)} <span>${range}</span></p>
              <div class="ac-bk-times__row">
                ${timeSlots
                    .filter((s) => s.period === period)
                    .map((s) => {
                        const free = this.courtsFreeAt(info, s.value).length;
                        const passed = courts.some(
                            (c) => info.perCourt[c.id].slots.find((x) => x.value === s.value)?.reason === "Passed"
                        );
                        const selected = this.draft.slot === s.value;
                        const text = free ? courtsText(free) : passed ? _t("Passed") : _t("Full");
                        return `
                    <button type="button" class="ac-bk-time${selected ? " is-selected" : ""}" data-bk-slot="${s.value}" aria-pressed="${selected}" ${free ? "" : "disabled"}
                            aria-label="${s.label}, ${free ? _t("%(free)s of %(total)s courts free", { free, total: courts.length }) : passed ? _t("time has passed") : _t("fully booked")}">
                      <strong>${s.label}</strong>
                      <span class="ac-bk-time__dots" aria-hidden="true">${courts.map((_c, i) => `<i class="${i < free ? "ac-on" : ""}"></i>`).join("")}</span>
                      <small>${text}</small>
                    </button>`;
                    })
                    .join("")}
              </div>
            </div>`
            )
            .join("");
    }

    extrasHTML() {
        const { rentalFee } = this.config;
        if (!this.draft.slot) {
            return `<p class="ac-bk-hint"><i class="ac-icon ac-i-ph-cursor-click-bold" aria-hidden="true"></i> ${_t("Select a time and we'll assign one of the free courts for you.")}</p>`;
        }
        return `
            <div class="ac-bk-extras">
              <label class="ac-extra-opt">
                <input type="checkbox" data-bk-rental ${this.draft.rental ? "checked" : ""} />
                <span class="ac-extra-opt__icon" aria-hidden="true"><i class="ac-icon ac-i-boxicons-shuttlecock-filled"></i></span>
                <span class="ac-extra-opt__text"><strong>${_t("Racket & shuttle rental")}</strong><small>${_t("Pro rackets and feather shuttles")}</small></span>
                <span class="ac-extra-opt__price">+${money(rentalFee)}<small>/${_t("member")}</small></span>
                <span class="ac-toggle__track" aria-hidden="true"><span class="ac-toggle__thumb"></span></span>
              </label>
              ${
                  this.draft.rental
                      ? `
              <div class="ac-rental-count">
                <p class="ac-bk-section-label" id="bkRentalLabel">${_t("How many members need rackets?")}</p>
                <div class="ac-bk-players" role="group" aria-labelledby="bkRentalLabel">
                  ${Array.from({ length: MAX_RENTALS }, (_, i) => i + 1)
                      .map(
                          (n) => `
                    <button type="button" class="ac-bk-player${this.draft.rentalCount === n ? " is-selected" : ""}" data-bk-rentals="${n}" aria-pressed="${this.draft.rentalCount === n}">
                      <strong>${n}</strong><small>${money(n * rentalFee)}</small>
                    </button>`
                      )
                      .join("")}
                </div>
              </div>`
                      : ""
              }
            </div>`;
    }

    footerHTML() {
        const ready = Boolean(this.draft.slot);
        const summary = ready
            ? `${this.slot.label} · ${_t("Court %s", this.court.number)}${this.rentals ? ` · ${rentalText(this.rentals)}` : ""}`
            : _t("Choose a time");
        return `
            <div class="ac-bk-flow__summary">
              <small>${summary}</small>
              <strong>${ready ? money(this.total) : `${this.config.currency}0`}</strong>
            </div>
            <button type="button" class="ac-btn ac-btn--primary" data-bk-action="to-details" ${ready ? "" : "disabled"}>
              ${_t("Book court")} <i class="ac-icon ac-i-ph-arrow-right-bold" aria-hidden="true"></i>
            </button>`;
    }

    async openTimes(iso, { swap = false } = {}) {
        const info = await this.waitFor(this.dayAvailability(iso));
        if (!swap || !this.draft || this.draft.date !== iso) {
            this.draft = { date: iso, slot: null, courtId: null, rental: false, rentalCount: 2 };
        }
        getModal().open(
            `
            <div class="ac-modal-content ac-bk-flow">
              ${this.flowSteps(0)}
              <div>
                <p class="ac-modal-sub">${_t("%s slots free this day", info.free)}</p>
                <h2 class="ac-modal-title" id="modalTitle" tabindex="-1">${longDate(iso)}</h2>
              </div>
              <div class="ac-bk-times" data-bk-times>${this.timesHTML(info)}</div>
              <div data-bk-extras>${this.extrasHTML()}</div>
              <div class="ac-bk-flow__footer" data-bk-footer>${this.footerHTML()}</div>
            </div>`,
            { wide: true, onClose: () => this.onFlowClose() }
        );
    }

    refreshTimesView() {
        const body = getModalBody();
        body.querySelector("[data-bk-times]").innerHTML = this.timesHTML(this.dayCache.get(this.draft.date));
        this.refreshExtras();
    }

    refreshExtras() {
        const body = getModalBody();
        body.querySelector("[data-bk-extras]").innerHTML = this.extrasHTML();
        body.querySelector("[data-bk-footer]").innerHTML = this.footerHTML();
    }

    /* ---------- modal view 2: details ---------- */
    openDetails() {
        const { draft, court, slot, rentals } = this;
        getModal().open(
            `
            <div class="ac-modal-content ac-bk-flow">
              ${this.flowSteps(1)}
              <div>
                <p class="ac-modal-sub">${_t("Review & your details")}</p>
                <h2 class="ac-modal-title" id="modalTitle" tabindex="-1">${_t("Confirm your court")}</h2>
              </div>
              <dl class="ac-detail-grid">
                <div><dt>${_t("Court")}</dt><dd>${_t("Court %s", court.number)} <small class="ac-muted-inline">(${_t("assigned")})</small></dd></div>
                <div><dt>${_t("Date")}</dt><dd>${formatDate(fromISODate(draft.date))}</dd></div>
                <div><dt>${_t("Time")}</dt><dd>${slotRange(slot)}</dd></div>
                <div><dt>${_t("Rental")}</dt><dd>${rentals ? `${rentalText(rentals)} · ${money(rentals * this.config.rentalFee)}` : _t("None")}</dd></div>
                <div><dt>${_t("Total")}</dt><dd class="ac-accent">${money(this.total)}</dd></div>
              </dl>
              <form class="ac-modal-form" data-bk-form="details" novalidate>
                <div class="ac-modal-form__grid">
                  <div class="ac-field">
                    <label class="ac-field__label" for="f-name">${_t("Full name")}</label>
                    <input class="ac-input" id="f-name" name="name" type="text" required autocomplete="name" value="${escapeHTML(draft.name || "")}" aria-describedby="f-name-error" />
                    <p class="ac-field__error" id="f-name-error" data-error-for="name"></p>
                  </div>
                  <div class="ac-field">
                    <label class="ac-field__label" for="f-phone">${_t("Mobile number")}</label>
                    <input class="ac-input" id="f-phone" name="phone" type="tel" required autocomplete="tel" inputmode="tel" placeholder="+1 555 123 4567" value="${escapeHTML(draft.phone || "")}" aria-describedby="f-phone-error f-phone-help" />
                    <p class="ac-field__error" id="f-phone-error" data-error-for="phone"></p>
                  </div>
                </div>
                <p class="ac-modal-note" id="f-phone-help"><i class="ac-icon ac-i-ph-device-mobile-bold" aria-hidden="true"></i> <span>${_t("Our team will call or message this number to confirm your booking.")}</span></p>
                <p class="ac-field__error" data-bk-error role="alert"></p>
                <div class="ac-modal-actions">
                  <button type="button" class="ac-btn ac-btn--ghost" data-bk-action="back-times"><i class="ac-icon ac-i-ph-arrow-left-bold" aria-hidden="true"></i> ${_t("Back")}</button>
                  <button type="submit" class="ac-btn ac-btn--primary"><span class="ac-btn__label">${_t("Confirm booking")}</span> <i class="ac-icon ac-i-ph-check-bold" aria-hidden="true"></i></button>
                </div>
              </form>
            </div>`,
            { wide: true, onClose: () => this.onFlowClose() }
        );
    }

    /* ---------- submit: the booking becomes a CRM lead ---------- */
    async submitBooking(form) {
        const button = form.querySelector('button[type="submit"]');
        const error = form.querySelector("[data-bk-error]");
        error.textContent = "";
        setLoading(button, true, _t("Booking…"));
        try {
            const { draft, slot, rentals } = this;
            const booking = await this.waitFor(
                bookingService.createBooking({
                    date: draft.date,
                    slot: draft.slot,
                    rentalCount: rentals,
                    name: draft.name,
                    phone: draft.phone,
                })
            );
            this.dayCache.delete(draft.date); // refresh this day's availability
            getModal().showSuccess({
                title: _t("Request received."),
                text: _t(
                    "Thanks, %(name)s! Court %(court)s is held for you on %(date)s at %(time)s. We will contact you shortly to confirm.",
                    {
                        name: escapeHTML(draft.name.split(" ")[0]),
                        court: booking.courtNumber,
                        date: longDate(draft.date),
                        time: slot.label,
                    }
                ),
                reference: booking.reference,
                details: [
                    [_t("Court"), _t("Court %s", booking.courtNumber)],
                    [_t("Time"), slotRange(slot)],
                    [_t("Rental"), rentalText(rentals)],
                    [_t("Total"), money(this.total)],
                ],
                note: _t("Payment is taken at the club. Keep your reference to change or cancel the booking."),
            });
        } catch (err) {
            error.textContent = err.message;
            this.dayCache.clear();
            bookingService.refresh();
        } finally {
            setLoading(button, false);
        }
    }

    onFlowClose() {
        this.draft = null;
        return this.renderCalendar();
    }

    /* ---------- modal events ---------- */
    onModalClick(ev) {
        if (!this.draft) {
            return;
        }
        const slotBtn = ev.target.closest("[data-bk-slot]");
        const rentalBtn = ev.target.closest("[data-bk-rentals]");
        const action = ev.target.closest("[data-bk-action]")?.dataset.bkAction;
        const body = getModalBody();

        if (slotBtn) {
            const firstPick = !this.draft.slot;
            this.draft.slot = slotBtn.dataset.bkSlot;
            this.draft.courtId = this.courtsFreeAt(this.dayCache.get(this.draft.date), this.draft.slot)[0]?.id || null;
            this.refreshTimesView();
            if (firstPick && window.matchMedia("(max-width: 720px)").matches) {
                const extras = body.querySelector("[data-bk-extras]");
                body.scrollTo({ top: extras.offsetTop - 24, behavior: prefersReducedMotion() ? "auto" : "smooth" });
            }
            body.querySelector(`[data-bk-slot="${this.draft.slot}"]`)?.focus({ preventScroll: true });
        } else if (rentalBtn) {
            this.draft.rentalCount = Number(rentalBtn.dataset.bkRentals);
            this.refreshExtras();
            body.querySelector(`[data-bk-rentals="${this.draft.rentalCount}"]`)?.focus({ preventScroll: true });
        } else if (action === "to-details") {
            this.openDetails();
        } else if (action === "back-times") {
            return this.openTimes(this.draft.date, { swap: true });
        }
    }

    onModalChange(ev) {
        if (!this.draft || !ev.target.matches("[data-bk-rental]")) {
            return;
        }
        this.draft.rental = ev.target.checked;
        this.refreshExtras();
        getModalBody().querySelector("[data-bk-rental]")?.focus({ preventScroll: true });
    }

    onModalSubmit(ev) {
        const form = ev.target.closest("form[data-bk-form]");
        if (!form || !this.draft) {
            return;
        }
        ev.preventDefault();
        if (!validateForm(form)) {
            return;
        }
        const phone = form.elements.phone.value.trim();
        const digits = phone.replace(/\D/g, "");
        if (digits.length < 7 || digits.length > 15) {
            fieldError(form, "phone", _t("Please enter a valid mobile number."));
            return;
        }
        this.draft.name = form.elements.name.value.trim();
        this.draft.phone = phone;
        return this.submitBooking(form);
    }
}

const category = registry.category("public.interactions");
category.add("theme_aerocourt.booking_rate", AcBookingRate);
category.add("theme_aerocourt.booking_calendar", AcBookingCalendar);
