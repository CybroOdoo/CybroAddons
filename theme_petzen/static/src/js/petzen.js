/**
 * Petzen theme — behaviour of the design, as Odoo 19 interactions:
 *   - preloader, scroll reveal, hero counters, back to top;
 *   - quick view of the product cards (adds to the cart with Odoo's cart
 *     service: variant / combo / optional products configurator included);
 *   - shop grid / list switch;
 *   - newsletter form of the footer (CRM lead);
 *   - products carousel (tabs, arrows, dots, autoplay, swipe), base of the
 *     "Petzen Products" snippet (products_snippet.js).
 */
import { _t } from "@web/core/l10n/translation";
import { rpc } from "@web/core/network/rpc";
import { registry } from "@web/core/registry";
import { escape } from "@web/core/utils/strings";
import { Interaction } from "@web/public/interaction";

// ── Preloader (home / reviews) ───────────────────────────────────────────────

export class PetzenPreloader extends Interaction {
    static selector = "#preloader";

    start() {
        // hidden by the .pl-done class (css/styles.css), the element stays in the
        // page so the website editor never saves the page without it
        const done = () => this.el.classList.add("pl-done");
        if (this.el.ownerDocument.readyState === "complete") {
            done();
        } else {
            this.addListener(window, "load", done, { once: true });
        }
        this.registerCleanup(() => this.el.classList.remove("pl-done"));
    }
}

// ── Page: reveal, counters, back to top, quick view, forms ──────────────────

export class PetzenPage extends Interaction {
    static selector = "#wrapwrap";
    dynamicContent = {
        // delegated: the product cards of the dynamic snippets are added later
        _root: {
            "t-on-click": this.onClick,
            "t-on-submit": this.onSubmit,
        },
    };

    setup() {
        this.doc = this.el.ownerDocument;
        this.overlay = this.el.querySelector("#qv-overlay");
        this.toast = this.el.querySelector("#petzen-toast");
        this.backToTop = this.el.querySelector("#btt");
    }

    start() {
        this.addListener(window, "scroll", this.onScroll, { passive: true });
        this.addListener(this.doc, "keydown", this.onKeydown);
        this.setupReveal();
        this.setupCounters();
        this.onScroll();
        this.registerCleanup(() => {
            this.revealObserver?.disconnect();
            this.counterObserver?.disconnect();
            this.doc.documentElement.classList.remove("pz-reveal-on");
            clearTimeout(this.toastTimer);
        });
    }

    // events -----------------------------------------------------------------

    /**
     * @param {MouseEvent} ev
     */
    onClick(ev) {
        const target = ev.target;
        if (target.closest("#btt")) {
            window.scrollTo({ top: 0, behavior: "smooth" });
        } else if (target.closest(".pz-shop-layout-btn")) {
            this.onShopLayoutChange(target.closest(".pz-shop-layout-btn"));
        } else if (target.closest(".pqv-btn")) {
            ev.preventDefault();
            ev.stopPropagation();
            this.openQuickView(target.closest(".product-card, .pz-tile"));
        } else if (target.closest("#qv-close") || target === this.overlay) {
            this.closeQuickView();
        } else if (target.closest("#qv-add-btn")) {
            this.onQuickViewAdd(target.closest("#qv-add-btn"));
        }
    }

    /**
     * @param {SubmitEvent} ev
     */
    onSubmit(ev) {
        if (ev.target.matches("#footer-nl-form")) {
            ev.preventDefault();
            this.onNewsletterSubmit(ev.target);
        }
    }

    onScroll() {
        this.backToTop?.classList.toggle("btt-show", window.scrollY > 600);
    }

    /**
     * @param {KeyboardEvent} ev
     */
    onKeydown(ev) {
        if (ev.key === "Escape") {
            this.closeQuickView();
        }
    }

    // helpers ----------------------------------------------------------------

    /**
     * Show a message in the toast of the design for 3 seconds.
     *
     * @param {string} msg
     * @param {boolean} [isError]
     */
    showToast(msg, isError) {
        if (!this.toast) {
            return;
        }
        this.toast.textContent = msg;
        this.toast.style.background = isError ? "#dc2626" : "#1A1208";
        this.toast.classList.add("show");
        clearTimeout(this.toastTimer);
        this.toastTimer = setTimeout(() => this.toast.classList.remove("show"), 3000);
    }

    /**
     * @param {boolean} lock
     */
    lockScroll(lock) {
        this.doc.body.style.overflow = lock ? "hidden" : "";
    }

    // reveal -----------------------------------------------------------------

    setupReveal() {
        const items = [...this.el.querySelectorAll(".reveal")];
        if (!items.length) {
            return;
        }
        if (!("IntersectionObserver" in window)) {
            items.forEach((el) => el.classList.add("in"));
            return;
        }
        // what is already on screen stays visible (no flash when the lazy assets start)
        const vh = window.innerHeight;
        items.forEach((el) => {
            const rect = el.getBoundingClientRect();
            if (rect.top < vh && rect.bottom > 0) {
                el.classList.add("in");
            }
        });
        this.doc.documentElement.classList.add("pz-reveal-on");
        this.revealObserver = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    const delay = parseFloat(entry.target.dataset.delay || 0);
                    setTimeout(() => entry.target.classList.add("in"), delay * 1000);
                    this.revealObserver.unobserve(entry.target);
                }
            });
        }, { threshold: 0.12 });
        items.filter((el) => !el.classList.contains("in")).forEach((el) => this.revealObserver.observe(el));
    }

    // hero counters ----------------------------------------------------------

    setupCounters() {
        const counters = this.el.querySelectorAll(".hero-stat-num[data-t]");
        if (!counters.length || !("IntersectionObserver" in window)) {
            counters.forEach((el) => (el.textContent = el.dataset.t + (+el.dataset.t >= 500 ? "+" : "")));
            return;
        }
        this.counterObserver = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                const el = entry.target;
                if (!entry.isIntersecting || el.dataset.done) {
                    return;
                }
                el.dataset.done = 1;
                this.counterObserver.unobserve(el);
                const target = +el.dataset.t;
                const step = Math.ceil(target / 45);
                let n = 0;
                const timer = setInterval(() => {
                    n = Math.min(n + step, target);
                    el.textContent = n + (target >= 500 ? "+" : "");
                    if (n >= target) {
                        clearInterval(timer);
                    }
                }, 30);
            });
        }, { threshold: 0.5 });
        counters.forEach((el) => this.counterObserver.observe(el));
    }

    // shop grid / list switch (views/shop_templates.xml) ---------------------

    /**
     * @param {HTMLElement} button
     */
    onShopLayoutChange(button) {
        const layout = button.dataset.pzLayout;
        const container = button.closest("#o_wsale_container");
        const grid = container?.querySelector("#o_wsale_products_grid");
        if (!grid || !["grid", "list"].includes(layout)) {
            return;
        }
        grid.classList.toggle("o_wsale_products_opt_layout_list", layout === "list");
        grid.classList.toggle("o_wsale_products_opt_layout_catalog", layout === "grid");
        container.querySelectorAll(".pz-shop-layout-btn").forEach((item) => {
            const active = item.dataset.pzLayout === layout;
            item.classList.toggle("active", active);
            item.setAttribute("aria-pressed", String(active));
        });
    }

    // quick view -------------------------------------------------------------

    /**
     * Fill the quick view with a design card (Petzen Products snippet) or an
     * Odoo shop tile (form.pz-tile) and open it.
     *
     * @param {HTMLElement} card
     */
    openQuickView(card) {
        const overlay = this.overlay;
        if (!card || !overlay) {
            return;
        }
        const text = (el) => (el ? el.textContent.replace(/\s+/g, " ").trim() : "");
        const img = card.querySelector(".product-img, .oe_product_image img");
        const ribbon = card.querySelector(".product-badge, .o_ribbons");
        const badge = ribbon && text(ribbon) ? ribbon : null;
        const price = card.querySelector(".product-price, .product_price > span");
        const priceOld = card.querySelector(".product-price-old, .product_price del");
        const stars = card.querySelector(".stars");
        const starCount = card.querySelector(".star-count");
        const name = card.querySelector(".product-name, .o_wsale_products_item_title a");
        // can be added to the cart (Odoo's add to cart button of the card / tile)
        const canAdd = !!card.querySelector(".s_add_to_cart_btn, .a-submit");
        const productId = card.dataset.productId || card.dataset.pzProductId || "";
        const templateId = card.dataset.templateId
            || card.querySelector("input[name=product_template_id]")?.value || "";

        const qvImg = overlay.querySelector("#qv-img");
        qvImg.src = img ? img.currentSrc || img.src : "";
        qvImg.alt = img ? img.alt : "";
        const qvBadge = overlay.querySelector("#qv-badge");
        qvBadge.textContent = badge ? text(badge) : "";
        qvBadge.className = "qv-badge" + (badge && !badge.classList.contains("product-badge") || badge?.classList.contains("new-badge") ? " new-b" : "");
        overlay.querySelector("#qv-name").textContent = text(name);
        overlay.querySelector("#qv-tag").textContent = text(card.querySelector(".product-tag"));
        overlay.querySelector("#qv-rating").innerHTML = (stars ? stars.outerHTML : "") + (starCount ? "&nbsp;" + starCount.outerHTML : "");
        overlay.querySelector("#qv-price-row").innerHTML =
            '<span class="qv-price">' + escape(text(price)) + "</span>" +
            (priceOld ? '<span class="qv-price-old">' + escape(text(priceOld)) + "</span>" : "");

        const addBtn = overlay.querySelector("#qv-add-btn");
        addBtn.dataset.canAdd = canAdd && templateId ? "1" : "";
        addBtn.dataset.productId = productId;
        addBtn.dataset.templateId = templateId;
        addBtn.dataset.productType = card.querySelector("[data-product-type]")?.dataset.productType || "";
        addBtn.dataset.url = card.dataset.url || card.querySelector("a[href]")?.getAttribute("href") || "";
        addBtn.innerHTML = addBtn.dataset.canAdd
            ? '<iconify-icon icon="lucide:shopping-bag" style="font-size:16px"></iconify-icon> ' + escape(_t("Add to Cart"))
            : '<iconify-icon icon="lucide:sliders-horizontal" style="font-size:16px"></iconify-icon> ' + escape(_t("Choose Options"));

        overlay.classList.add("open");
        this.lockScroll(true);
        overlay.querySelector("#qv-close")?.focus();
    }

    closeQuickView() {
        if (this.overlay?.classList.contains("open")) {
            this.overlay.classList.remove("open");
            this.lockScroll(false);
        }
    }

    /**
     * Add the product with Odoo's cart service, as the "Add" buttons of the
     * cards: added directly (Odoo's cart notification), or Odoo's variant /
     * combo / optional products configurator is opened. The quick view is
     * closed first so it never hides Odoo's dialogs.
     *
     * @param {HTMLElement} btn
     */
    async onQuickViewAdd(btn) {
        if (!btn.dataset.canAdd) {
            if (btn.dataset.url) {
                window.location.href = btn.dataset.url;
            }
            return;
        }
        this.closeQuickView();
        try {
            await this.waitFor(this.services.cart.add({
                productTemplateId: parseInt(btn.dataset.templateId),
                productId: parseInt(btn.dataset.productId) || undefined,
                isCombo: btn.dataset.productType === "combo",
            }));
        } catch {
            this.showToast(_t("Could not add this product to your cart."), true);
        }
    }

    // newsletter (footer) ----------------------------------------------------

    /**
     * @param {HTMLFormElement} form
     */
    async onNewsletterSubmit(form) {
        const input = form.querySelector("input[name=email]");
        const btn = form.querySelector("button[type=submit]");
        btn.disabled = true;
        try {
            const res = await this.waitFor(rpc("/petzen/newsletter", { email: input.value }));
            if (res.success) {
                form.reset();
                this.showToast(_t("Thanks for subscribing! 🐾"));
            } else {
                this.showToast(res.error, true);
            }
        } catch {
            this.showToast(_t("Network error. Please try again."), true);
        } finally {
            btn.disabled = false;
        }
    }
}

// ── Products carousel: tabs, arrows, dots, autoplay, swipe ──────────────────

/**
 * Base of the "Petzen Products" snippet interaction (products_snippet.js), which
 * inserts the tabs and the product cards then calls `start()`.
 */
export class PetzenProducts extends Interaction {
    dynamicContent = {
        _root: {
            "t-on-mouseenter": this.stopAuto,
            "t-on-mouseleave": this.startAuto,
            "t-on-focusin": this.stopAuto,
            "t-on-focusout": this.startAuto,
        },
        _window: { "t-on-resize": this.debounced(this.rebuild, 150) },
        ".tab-pill": { "t-on-click": this.onTabClick },
        ".c-prev": { "t-on-click": this.onPrev },
        ".c-next": { "t-on-click": this.onNext },
        ".c-dots": { "t-on-click": this.onDotClick },
    };
    DELAY = 3500;

    setup() {
        this.idx = 0;
        this.timer = null;
        this.isEditMode = false;
    }

    start() {
        this.row = this.el.querySelector(".products-row");
        this.outer = this.el.querySelector(".carousel-outer");
        this.dots = this.el.querySelector(".c-dots");
        // swipe on touch screens
        if (this.outer) {
            this.addListener(this.outer, "touchstart", this.onTouchStart, { passive: true });
            this.addListener(this.outer, "touchend", this.onTouchEnd, { passive: true });
        }
        this.registerCleanup(() => {
            this.stopAuto();
            if (this.row) {
                this.row.style.transform = "";
            }
            this.dots?.replaceChildren();
        });
        this.rebuild();
    }

    // filters ----------------------------------------------------------------

    /**
     * Show the cards of a tab ("all" = every card).
     *
     * @param {string} key
     */
    filter(key) {
        const pills = [...this.el.querySelectorAll(".tab-pill")];
        const match = pills.find((p) => p.dataset.f === key) || pills.find((p) => p.dataset.f === "all");
        pills.forEach((p) => p.classList.toggle("active", p === match));
        const f = match ? match.dataset.f : "all";
        this.row?.querySelectorAll(".product-card").forEach((card) => {
            card.style.display = f === "all" || card.dataset.cat === f ? "" : "none";
            card.classList.add("in"); // cards shown by a filter must not stay hidden by the reveal
        });
        this.idx = 0;
        this.rebuild();
    }

    /**
     * @param {MouseEvent} ev
     */
    onTabClick(ev) {
        this.filter(ev.currentTarget.dataset.f);
    }

    // carousel ---------------------------------------------------------------

    cards() {
        return [...(this.row?.querySelectorAll(".product-card") || [])].filter((c) => c.style.display !== "none");
    }

    step() {
        const card = this.cards()[0];
        if (!card) {
            return 0;
        }
        const gap = parseFloat(getComputedStyle(this.row).columnGap) || 0;
        return card.offsetWidth + gap;
    }

    visible() {
        const step = this.step();
        if (!step || !this.outer) {
            return 1;
        }
        const gap = parseFloat(getComputedStyle(this.row).columnGap) || 0;
        return Math.max(1, Math.round((this.outer.clientWidth + gap) / step));
    }

    maxIdx() {
        return Math.max(0, this.cards().length - this.visible());
    }

    /**
     * Rebuild the dots (one per position) and show the current position.
     */
    rebuild() {
        if (!this.row) {
            return;
        }
        if (this.dots) {
            const pages = this.maxIdx() + 1;
            const dots = [];
            // a single dot is useless (everything is visible)
            for (let i = 0; pages > 1 && i < pages; i++) {
                const dot = document.createElement("button");
                dot.type = "button";
                dot.className = "c-dot";
                dot.dataset.idx = i;
                dot.setAttribute("aria-label", _t("Go to slide %s", i + 1));
                dots.push(dot);
            }
            this.dots.replaceChildren(...dots);
        }
        this.update();
        this.startAuto();
    }

    update() {
        const max = this.maxIdx();
        this.idx = Math.min(Math.max(this.idx, 0), max);
        this.row.style.transform = this.idx ? `translateX(-${this.idx * this.step()}px)` : "";
        const prev = this.el.querySelector(".c-prev");
        const next = this.el.querySelector(".c-next");
        if (prev) {
            prev.disabled = this.idx <= 0;
            prev.classList.toggle("d-none", max < 1);
        }
        if (next) {
            next.disabled = this.idx >= max;
            next.classList.toggle("d-none", max < 1);
        }
        this.dots?.querySelectorAll(".c-dot").forEach((dot, i) => {
            dot.classList.remove("active");
            if (i === this.idx) {
                void dot.offsetWidth; // restart the progress animation
                dot.classList.add("active");
            }
        });
    }

    /**
     * @param {number} idx
     */
    goTo(idx) {
        this.idx = idx;
        this.update();
        this.startAuto();
    }

    onPrev() {
        this.goTo(this.idx - 1);
    }

    onNext() {
        this.goTo(this.idx + 1);
    }

    /**
     * @param {MouseEvent} ev
     */
    onDotClick(ev) {
        const dot = ev.target.closest(".c-dot");
        if (dot) {
            this.goTo(parseInt(dot.dataset.idx, 10) || 0);
        }
    }

    /**
     * @param {TouchEvent} ev
     */
    onTouchStart(ev) {
        const touch = ev.touches[0];
        this.touchStart = touch && { x: touch.clientX, y: touch.clientY };
        this.stopAuto();
    }

    /**
     * @param {TouchEvent} ev
     */
    onTouchEnd(ev) {
        const touch = ev.changedTouches[0];
        const start = this.touchStart;
        this.touchStart = null;
        if (!touch || !start) {
            return;
        }
        const dx = touch.clientX - start.x;
        // horizontal swipe only (vertical moves scroll the page)
        if (Math.abs(dx) > 40 && Math.abs(dx) > Math.abs(touch.clientY - start.y)) {
            this.goTo(this.idx + (dx < 0 ? 1 : -1));
        } else {
            this.startAuto();
        }
    }

    startAuto() {
        this.stopAuto();
        if (this.isEditMode || this.maxIdx() < 1) {
            return;
        }
        this.timer = setInterval(() => {
            this.idx = this.idx >= this.maxIdx() ? 0 : this.idx + 1;
            this.update();
        }, this.DELAY);
    }

    stopAuto() {
        clearInterval(this.timer);
        this.timer = null;
    }
}

registry.category("public.interactions").add("theme_petzen.preloader", PetzenPreloader);
registry.category("public.interactions").add("theme_petzen.page", PetzenPage);
// the preloader is also hidden in the website editor
registry.category("public.interactions.edit").add("theme_petzen.preloader", {
    Interaction: PetzenPreloader,
});
