/**
 * Propelle booking page.
 *
 * Four steps to request a viewing of a listing or a valuation visit. The
 * request is sent to the sales team as a lead; an agent confirms the time with
 * the visitor. An unfinished draft is remembered in the local storage.
 *
 *   /booking?type=sale|rent&home=<id>
 *   /booking?type=sell[&step=2&address=…&city=…]
 */
import { rpc } from "@web/core/network/rpc";
import { registry } from "@web/core/registry";
import { Interaction } from "@web/public/interaction";
import { prefersReducedMotion, showToast, store } from "@theme_propelle/js/propelle_core";

const DRAFT_KEY = "propelle-booking-draft";
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
const PHONE_RE = /^[+()\d\s.-]{7,20}$/;
const TEXT_FIELDS = [
    "bk-address",
    "bk-city",
    "bk-ptype",
    "bk-beds",
    "bk-name",
    "bk-email",
    "bk-phone",
    "bk-notes",
];

const esc = (text) =>
    String(text)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
const iso = (d) =>
    `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
const fromIso = (s) => {
    const [y, m, d] = s.split("-").map(Number);
    return new Date(y, m - 1, d);
};
const fmtDay = (d) =>
    d.toLocaleDateString("en-US", { weekday: "short", day: "numeric", month: "short" });
const fmtLong = (d) =>
    d.toLocaleDateString("en-US", { weekday: "long", day: "numeric", month: "long" });
const hourLabel = (h) => `${h > 12 ? h - 12 : h}:00 ${h >= 12 ? "pm" : "am"}`;
// Opening hours: 9am to 5pm on weekdays, 10am to 3pm on Saturday
const openHours = (d) =>
    d.getDay() === 6 ? [10, 11, 12, 13, 14, 15] : [9, 10, 11, 12, 13, 14, 15, 16, 17];

export class PropelleBooking extends Interaction {
    static selector = ".pp-booking";

    setup() {
        this.form = this.el.querySelector("#booking-form");
        this.listings = JSON.parse(this.form.dataset.listings || "[]");
        this.days = JSON.parse(this.form.dataset.days || "[]").map(fromIso);
        this.query = new URLSearchParams(window.location.search);
        this.step = 1;
        this.confirmed = false;
        this.b = {
            status: this.query.get("type") === "rent" ? "rent" : "sale",
            home: null,
            kind: "In person",
            day: null,
            time: null,
        };
    }

    $(selector) {
        return this.el.querySelector(selector);
    }

    $$(selector) {
        return Array.from(this.el.querySelectorAll(selector));
    }

    field(id) {
        return this.el.querySelector("#" + id);
    }

    setup_mode() {
        this.mode = this.query.get("type") === "sell" ? "sell" : "view";
    }

    start() {
        this.setup_mode();
        this.applyMode();
        this.bindEvents();
        this.renderDays();
        if (this.mode === "view") {
            const pre = this.listings.find((l) => l.id === this.query.get("home"));
            if (pre) {
                this.b.home = pre.id;
                this.b.status = pre.status;
            }
            this.setStatus(this.b.status);
        }
        this.renderTimes();
        this.summary();
        const draft = store.get(DRAFT_KEY, null);
        const arrived = this.query.get("home") || this.query.get("address");
        if (draft && draft.mode === this.mode && !arrived) {
            this.offerDraft(draft);
        }
        if (
            this.mode === "sell" &&
            this.field("bk-address").value.trim().length >= 5 &&
            this.query.get("step") === "2"
        ) {
            this.go(2);
        }
    }

    /* Wording and fields of a viewing or of a valuation */
    applyMode() {
        const q = this.query;
        if (this.mode === "sell") {
            this.$("[data-bk-title]").textContent = "Book a free valuation";
            this.$("[data-bk-lead]").textContent =
                "Tell us about your property and pick a time. A local agent will visit and give you a written price range.";
            this.$("[data-bk-crumb]").textContent = "Sell";
            this.$("[data-bk-crumb]").href = "/sell";
            this.$("[data-bk-crumb-current]").textContent = "Book a valuation";
            this.$("[data-step1-label]").textContent = "Property";
            this.$('[data-step="1"][data-mode="view"]').remove();
            this.$('[data-step="1"][data-mode="sell"]').hidden = false;
            this.$("[data-kind-wrap]").remove();
            this.$("[data-sum-kind]").remove();
            this.$("#bk-done-back").href = "/sell";
            this.$("#bk-done-back").textContent = "Back to Sell";
            this.$("#bk-done-day").textContent =
                "Your agent visits, looks round and talks you through recent sales nearby.";
            for (const key of ["address", "city", "ptype", "beds", "name", "email", "phone"]) {
                if (q.get(key)) {
                    this.field("bk-" + key).value = q.get(key);
                }
            }
        } else {
            this.$('[data-step="1"][data-mode="sell"]').remove();
        }
    }

    bindEvents() {
        const on = (el, type, handler) => el && this.addListener(el, type, handler);
        on(this.field("bk-home-search"), "input", () => this.renderHomes());
        for (const btn of this.$$("[data-bk-status]")) {
            on(btn, "click", () => {
                this.setStatus(btn.dataset.bkStatus);
                this.saveDraft();
            });
        }
        for (const radio of this.$$('input[name="kind"]')) {
            on(radio, "change", () => {
                this.b.kind = radio.value;
                this.summary();
                this.saveDraft();
            });
        }
        for (const id of ["bk-address", "bk-name", "bk-email", "bk-phone", "bk-notes"]) {
            on(this.field(id), "input", () => {
                this.summary();
                this.saveDraft();
            });
        }
        for (const id of ["bk-city", "bk-ptype", "bk-beds"]) {
            on(this.field(id), "change", () => {
                this.summary();
                this.saveDraft();
            });
        }
        for (const input of this.$$("#booking-form input")) {
            on(input, "input", () => {
                if (input.getAttribute("aria-invalid") === "true") {
                    this.setError(input, "");
                }
            });
        }
        on(this.field("bk-consent"), "change", () => {
            this.$("#bk-consent-error").textContent = "";
        });
        on(this.$("#bk-next"), "click", () => this.onNext());
        on(this.$("#bk-back"), "click", () => this.go(Math.max(1, this.step - 1)));
        for (const tab of this.$$("[data-step-tab]")) {
            on(tab, "click", () => {
                const target = Number(tab.dataset.stepTab);
                if (target < this.step && !this.confirmed) {
                    this.go(target);
                }
            });
        }
        // Enter in a text field moves to the next step instead of submitting
        on(this.form, "keydown", (ev) => {
            if (
                ev.key === "Enter" &&
                ev.target.matches(
                    "input:not([type=radio]):not([type=checkbox]):not([type=search])"
                )
            ) {
                ev.preventDefault();
                this.onNext();
            }
        });
        on(this.form, "submit", (ev) => ev.preventDefault());
    }

    /* Step 1: homes */
    renderHomes() {
        const box = this.$("#bk-homes");
        if (!box) {
            return;
        }
        const search = this.field("bk-home-search");
        const term = ((search && search.value) || "").trim().toLowerCase();
        const list = this.listings.filter(
            (l) =>
                l.status === this.b.status &&
                (!term || `${l.title} ${l.loc} ${l.type}`.toLowerCase().includes(term))
        );
        box.innerHTML = list.length
            ? list
                  .map(
                      (l) => `
            <label class="pp-bk-home">
              <input type="radio" name="home" value="${esc(l.id)}"${this.b.home === l.id ? " checked" : ""}>
              <span class="pp-bk-home__card">
                <img src="${esc(l.img)}" alt="" loading="lazy">
                <span class="pp-bk-home__text"><strong>${esc(l.title)}</strong><small>${esc(l.loc)}</small><em>${esc(l.price)}</em></span>
              </span>
            </label>`
                  )
                  .join("")
            : `<p class="pp-bk-times__empty">No homes match “${esc(term)}”. Try a city or area name.</p>`;
        for (const radio of box.querySelectorAll('input[name="home"]')) {
            radio.addEventListener("change", () => {
                this.b.home = radio.value;
                this.$("#bk-home-error").textContent = "";
                this.summary();
                this.saveDraft();
            });
        }
    }

    setStatus(status) {
        const b = this.b;
        b.status = status;
        for (const btn of this.$$("[data-bk-status]")) {
            const on = btn.dataset.bkStatus === status;
            btn.classList.toggle("pp-is-active", on);
            btn.setAttribute("aria-checked", String(on));
        }
        const seg = this.$(".pp-bk-seg");
        if (seg) {
            seg.dataset.active = status;
        }
        const current = this.listings.find((l) => l.id === b.home);
        if (b.home && current && current.status !== status) {
            b.home = null;
        }
        this.renderHomes();
        this.summary();
    }

    /* Step 2: days and times */
    renderDays() {
        const box = this.$("#bk-days");
        box.innerHTML = this.days
            .map(
                (d, i) => `
        <label class="pp-bk-day"><input type="radio" name="day" value="${i}"${this.b.day === i ? " checked" : ""}>
          <span><small>${d.toLocaleDateString("en-US", { weekday: "short" })}</small><strong>${d.getDate()}</strong><small>${d.toLocaleDateString("en-US", { month: "short" })}</small></span>
        </label>`
            )
            .join("");
        for (const radio of box.querySelectorAll('input[name="day"]')) {
            radio.addEventListener("change", () => {
                this.b.day = Number(radio.value);
                this.b.time = null;
                this.renderTimes();
                this.summary();
                this.saveDraft();
            });
        }
    }

    renderTimes() {
        const box = this.$("#bk-times");
        const hint = this.$("#bk-time-hint");
        if (this.b.day === null) {
            box.innerHTML = '<p class="pp-bk-times__empty">Pick a day to see available times.</p>';
            hint.textContent = "";
            return;
        }
        const d = this.days[this.b.day];
        hint.textContent = d.getDay() === 6 ? "· Saturday hours 10am to 4pm" : "";
        const slots = openHours(d).map((hour) => ({ hour, label: hourLabel(hour) }));
        if (!slots.length) {
            box.innerHTML = '<p class="pp-bk-times__empty">No times are open on this day.</p>';
            return;
        }
        box.innerHTML = slots
            .map(
                (s) =>
                    `<label class="pp-bk-time"><input type="radio" name="time" value="${esc(s.label)}" data-hour="${s.hour}"${this.b.time === s.label ? " checked" : ""}><span>${esc(s.label)}</span></label>`
            )
            .join("");
        for (const radio of box.querySelectorAll('input[name="time"]')) {
            radio.addEventListener("change", () => {
                this.b.time = radio.value;
                this.b.hour = Number(radio.dataset.hour);
                this.$("#bk-slot-error").textContent = "";
                this.summary();
                this.saveDraft();
            });
        }
    }

    /* Summary of the side panel */
    home() {
        return this.listings.find((l) => l.id === this.b.home);
    }

    summary() {
        const box = this.$("#bk-sum-home");
        if (this.mode === "sell") {
            const address = this.field("bk-address").value.trim();
            box.innerHTML = address
                ? `<div class="pp-bk-summary__text"><small>Valuation of</small><strong>${esc(address)}</strong><span>${esc(this.field("bk-city").value)} · ${esc(this.field("bk-ptype").value)}</span></div>`
                : '<p class="pp-bk-summary__empty">No property entered yet</p>';
        } else {
            const h = this.home();
            box.innerHTML = h
                ? `<img src="${esc(h.img)}" alt=""><div class="pp-bk-summary__text"><strong>${esc(h.title)}</strong><span>${esc(h.loc)}</span><em>${esc(h.price)}</em></div>`
                : '<p class="pp-bk-summary__empty">No home selected yet</p>';
        }
        this.$("#bk-sum-date").textContent =
            this.b.day === null ? "Not chosen" : fmtDay(this.days[this.b.day]);
        this.$("#bk-sum-time").textContent = this.b.time || "Not chosen";
        const kind = this.$("#bk-sum-kind");
        if (kind) {
            kind.textContent = this.b.kind;
        }
        this.$("#bk-sum-name").textContent = this.field("bk-name").value.trim() || "Not given";
    }

    /* Draft: an unfinished booking is kept in this browser */
    saveDraft() {
        if (this.confirmed) {
            return;
        }
        const values = {};
        for (const id of TEXT_FIELDS) {
            if (this.field(id)) {
                values[id] = this.field(id).value;
            }
        }
        const b = this.b;
        const hasContent =
            b.home ||
            b.day !== null ||
            (values["bk-address"] || "").trim() ||
            (values["bk-name"] || "").trim();
        if (!hasContent) {
            return;
        }
        store.set(DRAFT_KEY, {
            mode: this.mode,
            status: b.status,
            home: b.home,
            kind: b.kind,
            date: b.day === null ? null : iso(this.days[b.day]),
            time: b.time,
            hour: b.hour,
            step: this.step,
            values,
            saved: Date.now(),
        });
    }

    applyState(s) {
        const b = this.b;
        if (s.status) {
            this.setStatus(s.status);
        }
        if (s.home) {
            b.home = s.home;
            this.setStatus(b.status);
        }
        b.kind = s.kind || "In person";
        const kind = this.$(`input[name="kind"][value="${b.kind}"]`);
        if (kind) {
            kind.checked = true;
        }
        const index = s.date ? this.days.findIndex((d) => iso(d) === s.date) : -1;
        b.day = index > -1 ? index : null;
        b.time = index > -1 ? s.time : null;
        b.hour = index > -1 ? s.hour : undefined;
        for (const [id, value] of Object.entries(s.values || {})) {
            if (this.field(id)) {
                this.field(id).value = value;
            }
        }
        this.renderHomes();
        this.renderDays();
        this.renderTimes();
        this.summary();
    }

    offerDraft(draft) {
        const home = draft.home && this.listings.find((l) => l.id === draft.home);
        const what = draft.home
            ? (home && home.title) || "a home"
            : (draft.values && draft.values["bk-address"]) || "your property";
        this.$("#bk-notice-text").innerHTML =
            `You have an unfinished booking for <strong>${esc(what)}</strong>. Pick up where you left off?`;
        this.$("#bk-notice").hidden = false;
        this.addListener(this.$("#bk-resume"), "click", () => {
            this.applyState(draft);
            this.$("#bk-notice").hidden = true;
            this.go(Math.min(draft.step || 1, 3));
        });
        this.addListener(this.$("#bk-discard"), "click", () => {
            store.remove(DRAFT_KEY);
            this.$("#bk-notice").hidden = true;
        });
    }

    /* Validation per step */
    setError(input, message) {
        const field = input.closest(".pp-field");
        field.classList.toggle("pp-has-error", Boolean(message));
        input.setAttribute("aria-invalid", message ? "true" : "false");
        field.querySelector(".pp-field__error").textContent = message || "";
    }

    validate(n) {
        const b = this.b;
        if (n === 1 && this.mode === "view" && !b.home) {
            this.$("#bk-home-error").textContent = "Please choose a home to view.";
            return false;
        }
        if (n === 1 && this.mode === "sell") {
            const address = this.field("bk-address");
            const ok = address.value.trim().length >= 5;
            this.setError(address, ok ? "" : "Please enter the property address.");
            if (!ok) {
                address.focus();
                return false;
            }
        }
        if (n === 2 && (b.day === null || !b.time)) {
            this.$("#bk-slot-error").textContent =
                b.day === null ? "Please choose a day." : "Please choose a time.";
            return false;
        }
        if (n === 3) {
            const name = this.field("bk-name");
            const email = this.field("bk-email");
            const phone = this.field("bk-phone");
            const checks = [
                [name, name.value.trim().length >= 2 ? "" : "Please enter your name."],
                [email, EMAIL_RE.test(email.value.trim()) ? "" : "Please enter a valid email address."],
                [
                    phone,
                    PHONE_RE.test(phone.value.trim())
                        ? ""
                        : "Please enter a phone number we can call.",
                ],
            ];
            for (const [input, message] of checks) {
                this.setError(input, message);
            }
            const bad = checks.find(([, message]) => message);
            if (bad) {
                bad[0].focus();
                return false;
            }
        }
        if (n === 4 && !this.field("bk-consent").checked) {
            this.$("#bk-consent-error").textContent =
                "Please tick the box so we can contact you about this booking.";
            return false;
        }
        return true;
    }

    /* Review of the last step */
    renderReview() {
        const rows = [];
        if (this.mode === "sell") {
            rows.push([
                "Property",
                `${esc(this.field("bk-address").value.trim())}<br><small>${esc(this.field("bk-city").value)} · ${esc(this.field("bk-ptype").value)} · ${esc(this.field("bk-beds").selectedOptions[0].textContent)} bed</small>`,
                1,
            ]);
        } else {
            const h = this.home();
            rows.push(["Home", `${esc(h.title)}<br><small>${esc(h.loc)} · ${esc(h.price)}</small>`, 1]);
            rows.push(["Viewing", esc(this.b.kind), 2]);
        }
        rows.push(["When", `${fmtLong(this.days[this.b.day])} at ${esc(this.b.time)}`, 2]);
        rows.push([
            "Contact",
            `${esc(this.field("bk-name").value.trim())}<br><small>${esc(this.field("bk-email").value.trim())} · ${esc(this.field("bk-phone").value.trim())}</small>`,
            3,
        ]);
        const notes = this.field("bk-notes").value.trim();
        if (notes) {
            rows.push(["Notes", esc(notes), 3]);
        }
        const review = this.$("#bk-review");
        review.innerHTML = rows
            .map(
                ([k, v, s]) =>
                    `<div><dt>${k}</dt><dd>${v}</dd><button type="button" class="pp-text-link" data-goto="${s}">Edit</button></div>`
            )
            .join("");
        for (const btn of review.querySelectorAll("[data-goto]")) {
            btn.addEventListener("click", () => this.go(Number(btn.dataset.goto)));
        }
    }

    /* Navigation */
    go(n) {
        this.step = n;
        for (const fieldset of this.$$(".pp-bk-step")) {
            fieldset.hidden = Number(fieldset.dataset.step) !== n;
        }
        for (const tab of this.$$("[data-step-tab]")) {
            const s = Number(tab.dataset.stepTab);
            tab.classList.toggle("pp-is-current", s === n);
            tab.classList.toggle("pp-is-done", s < n);
        }
        this.$("#bk-back").hidden = n === 1;
        const label =
            n === 4 ? "Send request" : "Continue";
        this.$("#bk-next").innerHTML =
            `${label} <i class="pp-icon pp-icon--sm pp-i-${n === 4 ? "check" : "arrow"}" role="img" aria-hidden="true"></i>`;
        if (n === 4) {
            this.renderReview();
        }
        const legend = this.$(`.pp-bk-step[data-step="${n}"] .pp-bk-step__title`);
        if (legend) {
            legend.setAttribute("tabindex", "-1");
            legend.focus({ preventScroll: true });
        }
        const top = this.$(".pp-bk-steps").getBoundingClientRect().top + window.scrollY - 100;
        if (window.scrollY > top) {
            window.scrollTo({ top, behavior: prefersReducedMotion() ? "auto" : "smooth" });
        }
        this.saveDraft();
    }

    onNext() {
        if (!this.validate(this.step)) {
            return;
        }
        if (this.step < 4) {
            this.go(this.step + 1);
        } else {
            this.confirmBooking();
        }
    }

    /* Confirmation: the request is sent to the sales team as a lead */
    async confirmBooking() {
        const b = this.b;
        const next = this.$("#bk-next");
        next.disabled = true;
        const date = this.days[b.day];
        const h = this.home();
        const payload = {
            mode: this.mode,
            date: iso(date),
            hour: b.hour,
            name: this.field("bk-name").value.trim(),
            email: this.field("bk-email").value.trim(),
            phone: this.field("bk-phone").value.trim(),
            notes: this.field("bk-notes").value.trim(),
        };
        if (this.mode === "sell") {
            Object.assign(payload, {
                address: this.field("bk-address").value.trim(),
                city: this.field("bk-city").value,
                ptype: this.field("bk-ptype").value,
                beds: this.field("bk-beds").value,
            });
        } else {
            Object.assign(payload, { home: b.home, kind: b.kind });
        }
        let result;
        try {
            result = await this.waitFor(rpc("/propelle/booking/request", payload));
        } catch {
            result = { error: "Something went wrong, please try again." };
        }
        next.disabled = false;
        if (result.error) {
            this.$("#bk-consent-error").textContent = result.error;
            return;
        }
        store.remove(DRAFT_KEY);
        this.confirmed = true;

        const first = esc(payload.name.split(" ")[0]);
        const what =
            this.mode === "sell"
                ? `valuation of ${esc(payload.address)}`
                : `${b.kind === "Video call" ? "video viewing" : "viewing"} of ${esc(h.title)}`;
        const office =
            this.mode === "sell" ? payload.city : esc(h.loc.split(", ").slice(-2, -1)[0]);
        this.$("#bk-done h2").textContent = "Request received";
        this.$("#bk-ref").textContent = result.reference;
        this.$("#bk-done-text").innerHTML =
            `Thanks, ${first}. We received your request for a ${what} on <strong>${fmtLong(date)} at ${esc(b.time)}</strong>. An agent from our ${esc(office)} office will contact you to confirm the time.`;
        if (this.mode === "view" && b.kind === "Video call") {
            this.$("#bk-done-day").textContent =
                "Your agent sends a video link 15 minutes before the call.";
        }
        for (const fieldset of this.$$(".pp-bk-step")) {
            fieldset.hidden = true;
        }
        this.$("#bk-nav").hidden = true;
        this.$("#bk-notice").hidden = true;
        for (const tab of this.$$("[data-step-tab]")) {
            tab.classList.remove("pp-is-current");
            tab.classList.add("pp-is-done");
        }
        this.$("#bk-done").hidden = false;
        this.$("#bk-done").focus();
        showToast(`Request sent: ${result.reference}`);
    }
}

registry.category("public.interactions").add("theme_propelle.booking", PropelleBooking);
