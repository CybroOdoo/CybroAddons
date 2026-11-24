/**
 * Nutivo snippets.
 *
 * Product grids (Bestsellers, Gift Hampers) filled with the shop products,
 * the testimonials slider, the animated FAQ accordion, the themed sort menus
 * and the shop filters of the Nutivo design. Every change made to the page is undone when
 * the interactions stop, so the edit mode only saves the snippet markup.
 */
import { markup } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";
import { registry } from "@web/core/registry";
import { setElementContent } from "@web/core/utils/html";
import { Interaction } from "@web/public/interaction";

const prefersReducedMotion = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;

/**
 * Product grid: cards of the shop products with category chips and sort.
 *
 * Options are read from the snippet: `data-card` (product or hamper),
 * `data-limit`, `data-categories` (categories in the filter chips) and
 * `data-category` (a category id or name).
 */
export class NutivoProductGrid extends Interaction {
    static selector = ".s_nutivo_bestsellers, .s_nutivo_hampers";

    setup() {
        this.grid = this.el.querySelector("[data-nv-grid]");
        this.chips = this.el.querySelector("[data-nv-chips]");
        this.sort = this.el.querySelector("[data-nv-sort]");
        this.category = this.el.dataset.category || "all";
        this.seq = 0;
    }

    async willStart() {
        if (this.grid) {
            await this.load(Boolean(this.chips));
        }
    }

    start() {
        if (this.chips) {
            this.addListener(this.chips, "click", this.onChipClick);
        }
        if (this.sort) {
            this.addListener(this.sort, "change", () => this.load(false));
        }
        this.registerCleanup(() => {
            this.ctx?.revert();
            this.grid?.replaceChildren();
            this.chips?.replaceChildren();
        });
    }

    async load(withChips) {
        const seq = ++this.seq;
        const result = await this.waitFor(
            rpc("/theme_nutivo/products", {
                category: this.category,
                limit: parseInt(this.el.dataset.limit) || 8,
                sort: this.sort ? this.sort.value : "featured",
                card: this.el.dataset.card || "product",
                chips: withChips,
                max_categories: parseInt(this.el.dataset.categories) || 5,
            })
        );
        if (seq !== this.seq) {
            return;
        }
        if (withChips && result.chips) {
            setElementContent(this.chips, markup(result.chips));
        }
        setElementContent(this.grid, markup(result.html));
        this.animate();
    }

    onChipClick(ev) {
        const chip = ev.target.closest(".nv-chip");
        if (!chip) {
            return;
        }
        for (const other of this.chips.querySelectorAll(".nv-chip")) {
            const on = other === chip;
            other.classList.toggle("nv-is-active", on);
            other.setAttribute("aria-selected", on);
        }
        this.category = chip.dataset.cat;
        this.load(false);
    }

    /** Stagger the new cards in, as the design does on page load. */
    animate() {
        const cards = [...this.grid.querySelectorAll(".nv-pcard, .nv-hamper")];
        const { gsap, ScrollTrigger } = window;
        if (!cards.length) {
            return;
        }
        if (!gsap || !ScrollTrigger || prefersReducedMotion()) {
            cards.forEach((card) => card.classList.add("nv-is-visible"));
            return;
        }
        gsap.registerPlugin(ScrollTrigger);
        this.ctx?.revert();
        this.ctx = gsap.context(() => {
            gsap.set(cards, { opacity: 0, y: 60 });
            ScrollTrigger.batch(cards, {
                start: "top 94%",
                once: true,
                onEnter: (batch) => this.ctx.add(() => {
                    gsap.to(batch, {
                        opacity: 1, y: 0, duration: 1.1, ease: "expo.out", stagger: 0.08,
                        clearProps: "transform,opacity",
                        onComplete: () => batch.forEach((card) => card.classList.add("nv-is-visible")),
                    });
                }),
            });
        }, this.grid);
    }
}

/** Testimonials slider: one card per step, wrapping at both ends. */
export class NutivoTestimonials extends Interaction {
    static selector = ".s_nutivo_testimonials";
    dynamicContent = {
        "[data-nv-slide='prev']": { "t-on-click": () => this.go(-1) },
        "[data-nv-slide='next']": { "t-on-click": () => this.go(1) },
        ".nv-testi-track": { "t-on-keydown": this.onKeydown },
    };

    setup() {
        this.track = this.el.querySelector(".nv-testi-track");
    }

    step() {
        const card = this.track.querySelector(".nv-testi");
        const gap = parseFloat(getComputedStyle(this.track).columnGap) || 24;
        return card ? card.getBoundingClientRect().width + gap : 300;
    }

    go(dir) {
        const track = this.track;
        const max = track.scrollWidth - track.clientWidth - 4;
        if (dir > 0 && track.scrollLeft >= max) {
            track.scrollTo({ left: 0 });
        } else if (dir < 0 && track.scrollLeft <= 4) {
            track.scrollTo({ left: track.scrollWidth });
        } else {
            track.scrollBy({ left: dir * this.step() });
        }
    }

    onKeydown(ev) {
        if (ev.key === "ArrowRight") {
            ev.preventDefault();
            this.go(1);
        } else if (ev.key === "ArrowLeft") {
            ev.preventDefault();
            this.go(-1);
        }
    }
}

/** FAQ: smooth open and close, one answer open at a time. */
export class NutivoAccordion extends Interaction {
    static selector = ".nv-faq__list";
    static DURATION = 420;
    static EASE = "cubic-bezier(.2, .7, .2, 1)";

    start() {
        this.wraps = [];
        for (const item of this.el.querySelectorAll(".nv-faq__item")) {
            const summary = item.querySelector("summary");
            if (!summary) {
                continue;
            }
            // Wrap the answer so that its height can animate without margin jumps.
            if (!item.querySelector(".nv-faq__answer")) {
                const wrap = this.el.ownerDocument.createElement("div");
                wrap.className = "nv-faq__answer";
                while (summary.nextSibling) {
                    wrap.append(summary.nextSibling);
                }
                item.append(wrap);
                this.wraps.push(wrap);
            }
            item.classList.toggle("nv-is-open", item.open);
            summary.setAttribute("aria-expanded", item.open);
        }
        this.addListener(this.el, "click", this.onClick);
        this.registerCleanup(() => {
            for (const wrap of this.wraps) {
                wrap.replaceWith(...wrap.childNodes);
            }
            for (const item of this.el.querySelectorAll(".nv-faq__item")) {
                item.classList.remove("nv-is-open");
                item.querySelector("summary")?.removeAttribute("aria-expanded");
            }
        });
    }

    animate(el, from, to) {
        el.getAnimations().forEach((anim) => anim.cancel());
        return el.animate(
            [
                { height: from, opacity: from === "0px" ? 0 : 1 },
                { height: to, opacity: to === "0px" ? 0 : 1 },
            ],
            {
                duration: prefersReducedMotion() ? 0 : NutivoAccordion.DURATION,
                easing: NutivoAccordion.EASE,
            }
        );
    }

    open(item) {
        const panel = item.querySelector(".nv-faq__answer");
        item.open = true;
        item.classList.add("nv-is-open");
        item.querySelector("summary").setAttribute("aria-expanded", "true");
        this.animate(panel, "0px", `${panel.scrollHeight}px`);
    }

    close(item) {
        const panel = item.querySelector(".nv-faq__answer");
        // The icon turns back straight away.
        item.classList.remove("nv-is-open");
        item.querySelector("summary").setAttribute("aria-expanded", "false");
        const anim = this.animate(panel, `${panel.offsetHeight}px`, "0px");
        anim.onfinish = () => {
            if (!item.classList.contains("nv-is-open")) {
                item.open = false;
            }
        };
    }

    onClick(ev) {
        const summary = ev.target.closest(".nv-faq__item > summary");
        if (!summary) {
            return;
        }
        // Driven here so that it can animate.
        ev.preventDefault();
        const item = summary.parentElement;
        if (item.classList.contains("nv-is-open")) {
            this.close(item);
            return;
        }
        for (const other of this.el.querySelectorAll(".nv-faq__item.nv-is-open")) {
            if (other !== item) {
                this.close(other);
            }
        }
        this.open(item);
    }
}

let selectSeq = 0;

/**
 * Themed dropdown replacing the option list of the browser. The real
 * <select> stays in the page, hidden, and still fires `change`.
 */
export class NutivoSelect extends Interaction {
    static selector = ".nv-select-wrap";

    start() {
        const select = this.el.querySelector("select");
        if (!select || this.el.classList.contains("nv-is-enhanced")) {
            return;
        }
        const doc = this.el.ownerDocument;
        const name = this.el.querySelector(".nv-sr-only")?.textContent.trim() || "Choose an option";
        const prefix = select.dataset.prefix || "";
        const uid = `nv_sel${++selectSeq}`;
        this.select = select;
        this.el.classList.add("nv-is-enhanced");
        select.hidden = true;
        select.tabIndex = -1;

        const btn = doc.createElement("button");
        btn.type = "button";
        btn.className = "nv-select__btn";
        btn.setAttribute("aria-haspopup", "listbox");
        btn.setAttribute("aria-expanded", "false");
        btn.setAttribute("aria-controls", `${uid}_list`);
        const list = doc.createElement("ul");
        list.className = "nv-select__list";
        list.id = `${uid}_list`;
        list.setAttribute("role", "listbox");
        list.setAttribute("aria-label", name);
        list.tabIndex = -1;
        [...select.options].forEach((option, i) => {
            const li = doc.createElement("li");
            li.className = "nv-select__opt";
            li.setAttribute("role", "option");
            li.id = `${uid}_o${i}`;
            li.dataset.value = option.value;
            const label = doc.createElement("span");
            label.textContent = option.textContent.trim();
            const check = doc.createElement("i");
            check.className = "nv-i nv-ph-check-light";
            check.setAttribute("aria-hidden", "true");
            li.append(label, check);
            list.append(li);
        });
        this.insert(btn);
        this.insert(list);
        this.btn = btn;
        this.list = list;
        this.opts = [...list.querySelectorAll(".nv-select__opt")];
        this.active = select.selectedIndex;
        this.name = name;
        this.prefix = prefix;

        this.addListener(btn, "click", () => (this.el.classList.contains("nv-is-open") ? this.close() : this.open()));
        this.addListener(btn, "keydown", (ev) => {
            if (["ArrowDown", "ArrowUp", "Enter", " "].includes(ev.key)) {
                ev.preventDefault();
                this.open();
            }
        });
        this.addListener(list, "click", (ev) => {
            // The wrapper is a <label>: do not forward the click to the hidden select.
            ev.preventDefault();
            const opt = ev.target.closest(".nv-select__opt");
            if (opt) {
                this.choose(this.opts.indexOf(opt));
            }
        });
        this.addListener(list, "mousemove", (ev) => {
            const opt = ev.target.closest(".nv-select__opt");
            if (opt && this.opts.indexOf(opt) !== this.active) {
                this.setActive(this.opts.indexOf(opt));
            }
        });
        this.addListener(list, "keydown", this.onListKeydown);
        this.addListener(list, "focusout", (ev) => {
            if (!this.el.contains(ev.relatedTarget)) {
                this.close(false);
            }
        });
        this.addListener(doc, "click", (ev) => {
            if (!this.el.contains(ev.target)) {
                this.close(false);
            }
        });
        this.addListener(select, "change", this.paint);
        this.paint();
        this.registerCleanup(() => {
            select.hidden = false;
            select.removeAttribute("tabindex");
            this.el.classList.remove("nv-is-enhanced", "nv-is-open");
        });
    }

    paint() {
        const doc = this.el.ownerDocument;
        const i = this.select.selectedIndex;
        const label = this.select.options[i]?.textContent.trim() || "";
        const parts = [];
        if (this.prefix) {
            const pre = doc.createElement("span");
            pre.className = "nv-select__prefix";
            pre.textContent = this.prefix;
            parts.push(pre);
        }
        const value = doc.createElement("span");
        value.className = "nv-select__value";
        value.textContent = label;
        const caret = doc.createElement("i");
        caret.className = "nv-i nv-ph-caret-down-light";
        caret.setAttribute("aria-hidden", "true");
        this.btn.replaceChildren(...parts, value, caret);
        this.btn.setAttribute("aria-label", `${this.name}: ${label}`);
        this.opts.forEach((opt, k) => opt.setAttribute("aria-selected", k === i));
    }

    setActive(i) {
        this.active = Math.min(this.opts.length - 1, Math.max(0, i));
        this.opts.forEach((opt, k) => opt.classList.toggle("nv-is-active", k === this.active));
        this.list.setAttribute("aria-activedescendant", this.opts[this.active].id);
        this.opts[this.active].scrollIntoView({ block: "nearest" });
    }

    open() {
        this.el.classList.add("nv-is-open");
        this.btn.setAttribute("aria-expanded", "true");
        this.setActive(this.select.selectedIndex);
        this.waitForAnimationFrame(() => this.list.focus({ preventScroll: true }));
    }

    close(refocus = true) {
        if (!this.el.classList.contains("nv-is-open")) {
            return;
        }
        this.el.classList.remove("nv-is-open");
        this.btn.setAttribute("aria-expanded", "false");
        if (refocus) {
            this.btn.focus({ preventScroll: true });
        }
    }

    choose(i) {
        if (i !== this.select.selectedIndex) {
            this.select.selectedIndex = i;
            this.select.dispatchEvent(new Event("change", { bubbles: true }));
        }
        this.paint();
        this.close();
    }

    onListKeydown(ev) {
        const key = ev.key;
        if (key === "ArrowDown") {
            ev.preventDefault();
            this.setActive(this.active + 1);
        } else if (key === "ArrowUp") {
            ev.preventDefault();
            this.setActive(this.active - 1);
        } else if (key === "Home") {
            ev.preventDefault();
            this.setActive(0);
        } else if (key === "End") {
            ev.preventDefault();
            this.setActive(this.opts.length - 1);
        } else if (key === "Enter" || key === " ") {
            ev.preventDefault();
            this.choose(this.active);
        } else if (key === "Escape") {
            ev.preventDefault();
            ev.stopPropagation();
            this.close();
        } else if (key === "Tab") {
            this.close(false);
        } else if (key.length === 1) {
            // Type-ahead.
            const n = this.opts.length;
            for (let s = 1; s <= n; s++) {
                const i = (this.active + s) % n;
                if (this.opts[i].textContent.trim().toLowerCase().startsWith(key.toLowerCase())) {
                    this.setActive(i);
                    break;
                }
            }
        }
    }
}

const VIEW_KEY = "nutivo_shop_view_v2";
const VIEW_CLASSES = {
    catalog: "o_wsale_products_opt_layout_catalog",
    list: "o_wsale_products_opt_layout_list",
};

/**
 * Grid / list switch of the shop toolbar. It only swaps the layout class of the
 * product grid on the page, so every design option of the builder still
 * applies; the choice is remembered for the visitor and the page layout
 * is restored when the interaction stops.
 */
export class NutivoShopView extends Interaction {
    static selector = ".o_wsale_products_header_dropdown_wrap";
    dynamicContent = {
        ".nv-view-switch__btn": { "t-on-click": this.onClick },
    };

    setup() {
        this.grid = this.el.ownerDocument.querySelector("#o_wsale_products_grid");
        this.initial = this.grid
            ? Object.keys(VIEW_CLASSES).find((key) => this.grid.classList.contains(VIEW_CLASSES[key]))
            : null;
    }

    start() {
        if (!this.grid || !this.initial) {
            // Another layout (grid design): the switch does not apply.
            this.el.querySelector(".nv-view-switch")?.classList.add("d-none");
            return;
        }
        let view = this.initial;
        try {
            view = window.localStorage.getItem(VIEW_KEY) || this.initial;
        } catch {
            // Storage unavailable: keep the layout of the page.
        }
        this.setView(view);
        this.registerCleanup(() => this.setView(this.initial));
    }

    onClick(ev) {
        const view = ev.currentTarget.dataset.nvView;
        this.setView(view);
        try {
            window.localStorage.setItem(VIEW_KEY, view);
        } catch {
            // Storage unavailable: the choice lasts for this page only.
        }
    }

    setView(view) {
        if (!VIEW_CLASSES[view]) {
            return;
        }
        for (const [key, cls] of Object.entries(VIEW_CLASSES)) {
            this.grid.classList.toggle(cls, key === view);
        }
        for (const btn of this.el.querySelectorAll(".nv-view-switch__btn")) {
            btn.setAttribute("aria-pressed", btn.dataset.nvView === view);
        }
    }
}

registry
    .category("public.interactions")
    .add("theme_nutivo.product_grid", NutivoProductGrid)
    .add("theme_nutivo.testimonials", NutivoTestimonials)
    .add("theme_nutivo.accordion", NutivoAccordion)
    .add("theme_nutivo.select", NutivoSelect)
    .add("theme_nutivo.shop_view", NutivoShopView);
