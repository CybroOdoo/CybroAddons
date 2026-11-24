/** Session cards: filters, sorting and the registration modal. */

import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { Interaction } from "@web/public/interaction";
import { AcInteraction } from "./base";
import { fieldHTML } from "./forms";
import { getModal } from "./modal";
import { escapeHTML } from "./utils";

/* The sessions are plain blocks of the page: the website editor changes their
   text and photos, and clones or removes a card. Everything below reads what
   is written on the card, nothing is kept in the script. */

const text = (el, selector) => el.querySelector(selector)?.textContent.replace(/\s+/g, " ").trim() || "";
const number = (value) => Number(String(value).replace(/[^\d.]/g, "")) || 0;

/** What a session card says, read from its markup. */
function cardData(card) {
    return {
        image: card.querySelector(".ac-session-card__media img"),
        level: text(card, ".ac-session-card__level"),
        spots: text(card, ".ac-session-card__spots"),
        category: text(card, ".ac-session-card__cat"),
        title: text(card, ".ac-session-card__title"),
        desc: text(card, ".ac-session-card__desc"),
        duration: text(card, ".ac-session-card__duration"),
        coach: text(card, ".ac-session-card__coach"),
        price: text(card, ".ac-session-card__price"),
        times: Array.from(card.querySelectorAll(".ac-time-chip span")).map((el) => el.textContent.trim()),
        chosen: card.querySelector(".ac-time-chip input:checked")?.closest(".ac-time-chip")?.textContent.trim() || "",
    };
}

const priceOf = (data) => (/free/i.test(data.price) ? 0 : number(data.price));

/** Opens the booking form of a session in the modal. */
function openSessionModal(card) {
    const s = cardData(card);
    const juniors = /junior/i.test(s.level);
    const image = s.image?.getAttribute("src");
    getModal().open(`
        ${image ? `<div class="ac-modal-hero"><img src="${escapeHTML(image)}" alt="${escapeHTML(s.image.getAttribute("alt") || "")}" /></div>` : ""}
        <div class="ac-modal-content">
          <p class="ac-modal-sub">${escapeHTML(s.category)} · ${escapeHTML(s.level)} · ${escapeHTML(s.duration)}</p>
          <h2 class="ac-modal-title" id="modalTitle" tabindex="-1">${escapeHTML(s.title)}</h2>
          <p class="ac-modal-lead">${escapeHTML(s.desc)}</p>
          <dl class="ac-detail-grid">
            <div><dt>${_t("Coach")}</dt><dd>${escapeHTML(s.coach)}</dd></div>
            <div><dt>${_t("Price")}</dt><dd class="ac-accent">${escapeHTML(s.price)}</dd></div>
            <div><dt>${_t("Availability")}</dt><dd>${escapeHTML(s.spots)}</dd></div>
          </dl>
          <form class="ac-modal-form" data-form="session" data-title="${escapeHTML(s.title)}" data-price="${priceOf(s)}" data-duration="${escapeHTML(s.duration)}" data-price-text="${escapeHTML(s.price)}" novalidate>
            <fieldset class="ac-times-field" aria-describedby="f-sessionTime-error">
              <legend class="ac-field__label">${_t("Choose a time")}</legend>
              <div class="ac-session-card__times">
                ${s.times
                    .map(
                        (t) => `
                  <label class="ac-time-chip"><input type="radio" name="sessionTime" value="${escapeHTML(t)}" required ${t === s.chosen ? "checked" : ""} /><span>${escapeHTML(t)}</span></label>`
                    )
                    .join("")}
              </div>
              <p class="ac-field__error" id="f-sessionTime-error" data-error-for="sessionTime"></p>
            </fieldset>
            <div class="ac-modal-form__grid">
              ${fieldHTML({ name: "name", label: juniors ? _t("Player name") : _t("Full name"), autocomplete: "name" })}
              ${fieldHTML({ name: "email", label: juniors ? _t("Parent / guardian email") : _t("Email"), type: "email", autocomplete: "email", placeholder: "you@example.com" })}
            </div>
            <div class="ac-modal-actions">
              <button type="submit" class="ac-btn ac-btn--primary"><span class="ac-btn__label">${_t("Confirm session")}</span> <i class="ac-icon ac-i-ph-arrow-right-bold" aria-hidden="true"></i></button>
              <button type="button" class="ac-btn ac-btn--ghost" data-modal-close>${_t("Cancel")}</button>
            </div>
            <p class="ac-modal-note"><i class="ac-icon ac-i-ph-info-bold" aria-hidden="true"></i> <span>${_t("Our team confirms your place by email. Payment is taken at the club.")}</span></p>
          </form>
        </div>`);
}

let cardCount = 0;

/** "Book session" button of a card: opens the form of that session in the modal. */
export class AcSessionBook extends Interaction {
    static selector = ".ac-session-book";
    dynamicContent = {
        _root: { "t-on-click": this.onClick },
    };

    setup() {
        // Cloned cards must not share their time chips: one radio group per card
        this.card = this.el.closest(".ac-session-card");
        const id = `ac-session-${++cardCount}`;
        const radios = Array.from(this.card.querySelectorAll('.ac-time-chip input[type="radio"]'));
        const names = radios.map((radio) => radio.name);
        radios.forEach((radio) => (radio.name = id));
        this.registerCleanup(() => radios.forEach((radio, i) => (radio.name = names[i])));
    }

    onClick() {
        openSessionModal(this.card);
    }
}

/** Sessions page: category chips, search, level, day and sort of the cards. */
export class AcSessionPrograms extends AcInteraction {
    static selector = "#sessionsPage, .s_aerocourt_programs";
    dynamicContent = {
        "#programCategories": { "t-on-click": this.onCategoryClick },
        "[data-category]": {
            "t-att-class": (el) => ({ "is-active": el.dataset.category === this.state.category }),
            "t-att-aria-pressed": (el) => String(el.dataset.category === this.state.category),
        },
        "#programSearch": { "t-on-input": this.debounced(this.onSearch, 150) },
        "#programLevel": { "t-on-change": (ev) => (this.state.level = ev.target.value) },
        "#programDay": { "t-on-change": (ev) => (this.state.day = ev.target.value) },
        "#programSort": { "t-on-change": (ev) => this.sortBy(ev.target.value) },
        "#programGrid .ac-session-card": {
            "t-att-class": (el) => ({ "is-hidden": !this.matches(el) }),
        },
        "#programCount": { "t-out": () => this.countText() },
        "#programEmpty": {
            "t-att-hidden": () => this.visible() > 0,
            "t-on-click": this.onEmptyClick,
        },
    };

    setup() {
        this.state = { category: "All", level: "any", day: "any", query: "" };
        this.grid = this.el.querySelector("#programGrid");
        this.cards = () => Array.from(this.grid.querySelectorAll(":scope > .ac-session-card"));
        // The order of the page, kept for "recommended" and to put back on stop
        this.pageOrder = this.cards();
        this.registerCleanup(() => this.pageOrder.forEach((card) => this.grid.append(card)));
    }

    willStart() {
        // Category chips, with their counts, from the categories written on the cards
        const categories = this.cards().map((card) => cardData(card).category);
        const unique = ["All", ...new Set(categories)];
        this.setHTML(
            this.el.querySelector("#programCategories"),
            unique
                .map((category) => {
                    const n = category === "All" ? categories.length : categories.filter((c) => c === category).length;
                    return `<button type="button" class="ac-filter" data-category="${escapeHTML(category)}">${escapeHTML(category)} <span>${n}</span></button>`;
                })
                .join("")
        );
    }

    matches(card) {
        const s = this.state;
        const d = cardData(card);
        return (
            (s.category === "All" || d.category === s.category) &&
            (s.level === "any" || d.level === s.level) &&
            (s.day === "any" || d.times.some((t) => t.startsWith(s.day))) &&
            (!s.query || `${d.title} ${d.desc} ${d.coach} ${d.category}`.toLowerCase().includes(s.query))
        );
    }

    visible() {
        return this.cards().filter((card) => this.matches(card)).length;
    }

    countText() {
        const n = this.visible();
        return n === 1 ? _t("%s programme", n) : _t("%s programmes", n);
    }

    sortBy(key) {
        const value = (card) => {
            const d = cardData(card);
            return { "price-asc": priceOf(d), "price-desc": -priceOf(d), duration: number(d.duration), spots: number(d.spots) }[key];
        };
        const cards = key === "recommended" ? this.pageOrder.filter((c) => this.grid.contains(c)) : this.cards().sort((a, b) => value(a) - value(b));
        cards.forEach((card) => this.grid.append(card));
    }

    onCategoryClick(ev) {
        const btn = ev.target.closest("[data-category]");
        if (btn) {
            this.state.category = btn.dataset.category;
        }
    }

    onSearch(ev) {
        this.state.query = ev.target.value.trim().toLowerCase();
    }

    onEmptyClick(ev) {
        if (ev.target.closest("[data-reset-filters]")) {
            Object.assign(this.state, { category: "All", level: "any", day: "any", query: "" });
            this.el.querySelector("#programSearch").value = "";
            this.el.querySelector("#programLevel").value = "any";
            this.el.querySelector("#programDay").value = "any";
        }
    }
}

const category = registry.category("public.interactions");
category.add("theme_aerocourt.session_book", AcSessionBook);
category.add("theme_aerocourt.session_programs", AcSessionPrograms);
