/**
 * Propelle listing interactions.
 *
 * The search panel of the home page, the filters and sorting of the Buy and
 * Rent pages, the favourites, the details dialog of a listing and the two
 * calculators. Every change made to the page is undone when the interactions
 * stop, so the edit mode only saves the snippet markup.
 */
import { registry } from "@web/core/registry";
import { Interaction } from "@web/public/interaction";
import { loadPropelleData, showToast, store } from "@theme_propelle/js/propelle_core";

const FAVOURITES_KEY = "propelle-favs";

const money = (amount) => "$" + Math.round(amount).toLocaleString("en-US");

/**
 * Search panel of the home page: the Buy / Rent switch, the budgets of the
 * chosen kind, and the hand off to the listing page with the filters in the
 * URL.
 */
export class PropelleSearchPanel extends Interaction {
    static selector = ".pp-search-panel";
    dynamicContent = {
        ".pp-seg__btn": { "t-on-click": this.onSegmentClick },
        _root: { "t-on-submit.prevent": this.onSubmit },
        _window: { "t-on-resize": this.moveSegmentIndicator },
    };

    async willStart() {
        this.data = await this.waitFor(loadPropelleData());
    }

    start() {
        this.status = "sale";
        this.budgetSelect = this.el.querySelector("#s-budget");
        this.originalBudgets = Array.from(this.budgetSelect.children);
        this.registerCleanup(() => this.budgetSelect.replaceChildren(...this.originalBudgets));
        this.setStatus("sale");
        this.registerCleanup(() => {
            this.el.querySelector(".pp-seg").classList.remove("pp-has-indicator");
        });
    }

    /**
     * Place the sliding indicator of the Buy / Rent switch under the active
     * button.
     */
    moveSegmentIndicator() {
        const segment = this.el.querySelector(".pp-seg");
        const active = segment.querySelector(".pp-seg__btn.pp-is-active");
        if (!active || !active.offsetWidth) {
            return;
        }
        // The class makes the switch the positioning parent, so it goes first.
        segment.classList.add("pp-has-indicator");
        segment.style.setProperty("--pp-seg-x", active.offsetLeft + "px");
        segment.style.setProperty("--pp-seg-w", active.offsetWidth + "px");
    }

    setStatus(status) {
        this.status = status;
        const segment = this.el.querySelector(".pp-seg");
        segment.dataset.active = status;
        for (const btn of this.el.querySelectorAll(".pp-seg__btn")) {
            const active = btn.dataset.status === status;
            btn.classList.toggle("pp-is-active", active);
            btn.setAttribute("aria-checked", String(active));
        }
        this.moveSegmentIndicator();
        const any = document.createElement("option");
        any.value = "0";
        any.textContent = this.data ? "Any budget" : this.originalBudgets[0]?.textContent;
        const options = [any];
        for (const budget of (this.data && this.data.budgets[status]) || []) {
            const opt = document.createElement("option");
            opt.value = budget.value;
            opt.textContent = budget.long_label;
            options.push(opt);
        }
        this.budgetSelect.replaceChildren(...options);
    }

    onSegmentClick(ev) {
        this.setStatus(ev.currentTarget.dataset.status);
    }

    onSubmit() {
        const query = new URLSearchParams();
        const location = this.el.querySelector("#s-location").value;
        const type = this.el.querySelector("#s-type").value;
        const budget = this.budgetSelect.value;
        if (location !== "all") {
            query.set("location", location);
        }
        if (type !== "all") {
            query.set("type", type);
        }
        if (budget !== "0") {
            query.set("max", budget);
        }
        const page = this.status === "rent" ? "/rent" : "/buy";
        const search = query.toString();
        window.location.href = page + (search ? "?" + search : "") + "#listings";
    }
}

/**
 * Filter bar of the Buy and Rent pages. The listings are filtered, sorted and
 * paged by the server, so a change of any choice reloads the page with the
 * choices in the URL (`/buy?location=Miami&type=villa`), without the choices
 * left at their default.
 */
export class PropelleListingFilters extends Interaction {
    static selector = ".pp-listings";
    dynamicContent = {
        "[data-listing-filters]": {
            "t-on-change": this.submit,
            "t-on-submit.prevent": this.submit,
        },
        "#f-sort": { "t-on-change": this.submit },
    };

    setup() {
        this.form = this.el.querySelector("[data-listing-filters]");
    }

    start() {
        // the other pages of the listings open on the listings, not on the title
        if (this.form && window.location.pathname.includes("/page/") && !window.location.hash) {
            this.el.scrollIntoView();
        }
    }

    submit() {
        if (!this.form) {
            return;
        }
        const query = new URLSearchParams();
        for (const [name, value] of new FormData(this.form)) {
            if (value && value !== "all" && value !== "0" && value !== "newest") {
                query.set(name, value);
            }
        }
        const sort = this.el.querySelector("#f-sort");
        if (sort && sort.value !== "newest") {
            query.set("sort", sort.value);
        }
        const search = query.toString();
        window.location.href = this.form.getAttribute("action") + (search ? "?" + search : "") + "#listings";
    }
}

/**
 * Favourite button of the listing cards, remembered in the browser.
 */
export class PropelleFavourite extends Interaction {
    static selector = ".pp-pcard";
    dynamicContent = {
        ".pp-fav-btn": { "t-on-click": this.onClick },
    };

    setup() {
        this.button = this.el.querySelector(".pp-fav-btn");
        this.id = this.el.dataset.id;
        this.title = this.el.querySelector(".pp-pcard__title").textContent;
    }

    start() {
        if (this.button) {
            this.setPressed(new Set(store.get(FAVOURITES_KEY, [])).has(this.id));
        }
    }

    setPressed(on) {
        this.button.setAttribute("aria-pressed", String(on));
        this.button.setAttribute(
            "aria-label",
            `${on ? "Remove" : "Save"} ${this.title} ${on ? "from" : "to"} favourites`
        );
    }

    onClick() {
        const favourites = new Set(store.get(FAVOURITES_KEY, []));
        const on = !favourites.has(this.id);
        if (on) {
            favourites.add(this.id);
        } else {
            favourites.delete(this.id);
        }
        store.set(FAVOURITES_KEY, Array.from(favourites));
        this.setPressed(on);
        showToast(on ? `Saved ${this.title}` : `Removed ${this.title}`);
    }
}

/**
 * Details dialog of the listing cards: it is filled from the card that was
 * clicked, and leads to the booking page with the home already chosen.
 */
export class PropelleDetails extends Interaction {
    static selector = ".pp-listings .pp-modal";
    dynamicContent = {
        _root: { "t-on-click": this.onModalClick },
        ".pp-modal__enquire": { "t-on-click": this.onEnquire },
    };

    setup() {
        this.modal = this.el;
        this.section = this.el.closest(".pp-listings");
        this.trigger = null;
        this.card = null;
    }

    start() {
        this.addListener(this.section, "click", this.onDetailsClick);
        this.addListener(this.modal, "close", this.onClose);
    }

    onDetailsClick(ev) {
        const button = ev.target.closest(".pp-js-details");
        if (!button || !this.section.contains(button)) {
            return;
        }
        this.trigger = button;
        this.open(button.closest(".pp-pcard"));
    }

    open(card) {
        const find = (selector) => card.querySelector(selector);
        const img = find("img");
        const status = card.dataset.status === "rent" ? "For rent" : "For sale";
        this.card = card;
        const modalImg = this.modal.querySelector(".pp-modal__img");
        modalImg.src = card.dataset.full || img.src;
        modalImg.alt = img.alt;
        this.modal.querySelector(".pp-modal__type").textContent =
            `${find(".pp-tag").textContent} · ${status}`;
        this.modal.querySelector(".pp-modal__title").textContent =
            find(".pp-pcard__title").textContent;
        this.modal.querySelector(".pp-modal__loc").innerHTML = find(".pp-pcard__loc").innerHTML;
        this.modal.querySelector(".pp-modal__price").innerHTML = find(".pp-pcard__price").innerHTML;
        this.modal.querySelector(".pp-modal__specs").innerHTML = find(".pp-pcard__specs").innerHTML;
        if (typeof this.modal.showModal === "function") {
            this.modal.showModal();
        } else {
            this.modal.setAttribute("open", "");
        }
        document.body.classList.add("pp-no-scroll");
    }

    close() {
        if (typeof this.modal.close === "function" && this.modal.open) {
            this.modal.close();
        } else {
            this.modal.removeAttribute("open");
            this.onClose();
        }
    }

    onClose() {
        document.body.classList.remove("pp-no-scroll");
        if (this.trigger) {
            this.trigger.focus();
        }
    }

    onModalClick(ev) {
        if (ev.target === this.modal || ev.target.closest("[data-close]")) {
            this.close();
        }
    }

    onEnquire(ev) {
        if (!this.card) {
            return;
        }
        const { status, id } = this.card.dataset;
        ev.currentTarget.href = `/booking?type=${status || "sale"}&home=${encodeURIComponent(id)}`;
    }

    destroy() {
        document.body.classList.remove("pp-no-scroll");
        if (this.modal.open) {
            this.modal.close();
        }
    }
}

/**
 * Mortgage calculator of the Buy page.
 */
export class PropelleMortgage extends Interaction {
    static selector = "#mortgage-form";
    dynamicContent = {
        _root: {
            "t-on-input": this.calculate,
            "t-on-change": this.calculate,
            "t-on-submit.prevent": this.calculate,
        },
    };

    start() {
        this.calculate();
    }

    out(id) {
        return this.el.closest("section").querySelector("#" + id);
    }

    calculate() {
        const num = (id) => Number(this.out(id).value) || 0;
        const price = Math.max(0, num("m-price"));
        const downPct = Math.min(100, Math.max(0, num("m-down")));
        const rate = Math.max(0, num("m-rate")) / 100 / 12;
        const months = num("m-term") * 12;
        const loan = price * (1 - downPct / 100);
        let monthly = 0;
        if (months) {
            monthly = rate === 0 ? loan / months : (loan * rate) / (1 - Math.pow(1 + rate, -months));
        }
        this.out("m-monthly").textContent = money(monthly);
        this.out("m-loan").textContent = money(loan);
        this.out("m-downpay").textContent = money(price - loan);
        this.out("m-interest").textContent = money(monthly * months - loan);
    }
}

/**
 * Affordability calculator of the Rent page.
 */
export class PropelleRentCalculator extends Interaction {
    static selector = "#rent-calc";
    dynamicContent = {
        _root: {
            "t-on-input": this.calculate,
            "t-on-change": this.calculate,
            "t-on-submit.prevent": this.calculate,
        },
    };

    start() {
        this.calculate();
    }

    out(id) {
        return this.el.closest("section").querySelector("#" + id);
    }

    calculate() {
        const income = Math.max(0, Number(this.out("rc-income").value) || 0);
        const debts = Math.max(0, Number(this.out("rc-debts").value) || 0);
        const share = Number(this.out("rc-share").value) / 100;
        // Rent target: share of the monthly income, less the monthly debts
        const monthly = Math.max(0, (income / 12) * share - debts);
        this.out("rc-max").textContent = money(monthly);
        // Landlords often ask for an income of 40 times the monthly rent
        this.out("rc-income-needed").textContent = money(monthly * 40);
        // First month and one month of deposit
        this.out("rc-deposit").textContent = money(monthly * 2);
    }
}

registry
    .category("public.interactions")
    .add("theme_propelle.search_panel", PropelleSearchPanel)
    .add("theme_propelle.listing_filters", PropelleListingFilters)
    .add("theme_propelle.favourite", PropelleFavourite)
    .add("theme_propelle.details", PropelleDetails)
    .add("theme_propelle.mortgage", PropelleMortgage)
    .add("theme_propelle.rent_calculator", PropelleRentCalculator);
