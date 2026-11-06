/** @odoo-module **/
/**
 * Petzen theme — behaviour of the design (preloader, reveal, counters, carousel,
 * quick view, back to top…) wired to Odoo instead of localStorage:
 *   - Quick View "Add to Cart" adds to the real website_sale cart (/shop/cart/update_json)
 *     (the "Add" and wishlist buttons of the cards: product_card.js)
 *   - newsletter / service booking create CRM leads
 */
import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";
import { escape } from "@web/core/utils/strings";
import { _t } from "@web/core/l10n/translation";

// ── helpers ──────────────────────────────────────────────────────────────────

function lockScroll(lock) {
    document.body.style.overflow = lock ? "hidden" : "";
}

/** Same feedback as the design: button turns into "✓ Added" for a moment. */
function flashAdded(btn, html, ms, background) {
    const orig = btn.innerHTML;
    btn.innerHTML = html;
    btn.classList.add("is-added");
    if (background) {
        btn.style.background = background;
    }
    setTimeout(() => {
        btn.innerHTML = orig;
        btn.classList.remove("is-added");
        btn.style.background = "";
    }, ms);
}

// ── Preloader (home / reviews) ───────────────────────────────────────────────

publicWidget.registry.PetzenPreloader = publicWidget.Widget.extend({
    selector: "#preloader",
    disabledInEditableMode: false,

    // Only hidden (pl-done), never removed from the page: the website editor saves
    // the page as it is in the DOM, a removed preloader would be lost for good.
    start() {
        this._onLoad = () => this.el.classList.add("pl-done");
        if (this.editableMode || document.readyState === "complete") {
            this._onLoad();
        } else {
            window.addEventListener("load", this._onLoad, { once: true });
        }
        return this._super(...arguments);
    },

    /** The class must not be saved in the page by the website editor. */
    destroy() {
        window.removeEventListener("load", this._onLoad);
        this.el.classList.remove("pl-done");
        this._super(...arguments);
    },
});

// ── Scroll reveal / counters / back to top / global overlays ────────────────

publicWidget.registry.PetzenPage = publicWidget.Widget.extend({
    selector: "#wrapwrap",
    events: {
        "click #btt": "_onBackToTop",
        "submit #footer-nl-form": "_onNewsletterSubmit",
        "click .pqv-btn": "_openQuickView",
        "click #qv-close": "_closeQuickView",
        "click #qv-overlay": "_onQuickViewOverlayClick",
        "click #qv-add-btn": "_onQuickViewAdd",
        "submit #booking-form": "_onBookingSubmit",
    },

    start() {
        this._onScroll = this._onScroll.bind(this);
        this._onKeydown = this._onKeydown.bind(this);
        window.addEventListener("scroll", this._onScroll, { passive: true });
        document.addEventListener("keydown", this._onKeydown);
        if (!this.editableMode) {
            this._setupReveal();
            this._setupCounters();
        }
        this._onScroll();
        return this._super(...arguments);
    },

    destroy() {
        window.removeEventListener("scroll", this._onScroll);
        document.removeEventListener("keydown", this._onKeydown);
        this.revealObserver?.disconnect();
        this.counterObserver?.disconnect();
        clearTimeout(this.toastTimer);
        document.documentElement.classList.remove("pz-reveal-on");
        this._super(...arguments);
    },

    // helpers --------------------------------------------------------------

    /** Show a short message in the toast of the overlays (views/layout.xml). */
    _showToast(msg, isError) {
        const toast = this.el.querySelector("#petzen-toast");
        if (!toast) {
            return;
        }
        toast.textContent = msg;
        toast.style.background = isError ? "#dc2626" : "#1A1208";
        toast.classList.add("show");
        clearTimeout(this.toastTimer);
        this.toastTimer = setTimeout(() => toast.classList.remove("show"), 3000);
    },

    /** Add one unit of a product variant to the website_sale cart and sync the badges. */
    async _addToCart(productId) {
        const data = await rpc("/shop/cart/update_json", {
            product_id: parseInt(productId, 10),
            add_qty: 1,
            display: false,
        });
        const qty = data.cart_quantity || 0;
        sessionStorage.setItem("website_sale_cart_quantity", qty);
        this.el.querySelectorAll(".my_cart_quantity").forEach((badge) => {
            badge.classList.remove("d-none", "fa", "fa-warning");
            badge.textContent = qty;
        });
        if (data.notification_info?.warning) {
            this._showToast(data.notification_info.warning, true);
        }
        // on the cart page the lines must be re-rendered by the server
        if (this.el.querySelector(".oe_cart .js_cart_lines")) {
            window.location.reload();
        }
        return data;
    },

    // reveal ---------------------------------------------------------------

    _setupReveal() {
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
        document.documentElement.classList.add("pz-reveal-on");
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
    },

    // hero counters --------------------------------------------------------

    _setupCounters() {
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
    },

    // scroll / keyboard ----------------------------------------------------

    _onScroll() {
        this.el.querySelector("#btt")?.classList.toggle("btt-show", window.scrollY > 600);
    },

    _onBackToTop() {
        window.scrollTo({ top: 0, behavior: "smooth" });
    },

    _onKeydown(ev) {
        if (ev.key === "Escape") {
            this._closeQuickView();
        }
    },

    // quick view -----------------------------------------------------------

    _openQuickView(ev) {
        ev.preventDefault();
        ev.stopPropagation();
        // Petzen Products snippet card or Odoo shop tile (form.pz-tile, see views/shop.xml)
        const card = ev.currentTarget.closest(".product-card, .pz-tile");
        const overlay = this.el.querySelector("#qv-overlay");
        if (!card || !overlay) {
            return;
        }
        const text = (el) => (el ? el.textContent.replace(/\s+/g, " ").trim() : "");
        const img = card.querySelector(".product-img, .oe_product_image img");
        const ribbon = card.querySelector(".product-badge, .o_ribbon");
        const badge = ribbon && text(ribbon) ? ribbon : null;
        const price = card.querySelector(".product-price, .product_price > span.h6");
        const priceOld = card.querySelector(".product-price-old, .product_price del");
        const stars = card.querySelector(".stars");
        const starCount = card.querySelector(".star-count");
        const name = card.querySelector(".product-name, .o_wsale_products_item_title a");
        const productId = card.dataset.productId || card.dataset.pzProductId || "";

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
        addBtn.dataset.productId = productId;
        addBtn.dataset.url = card.dataset.url || "";
        addBtn.innerHTML = productId
            ? '<iconify-icon icon="lucide:shopping-bag" style="font-size:16px"></iconify-icon> ' + escape(_t("Add to Cart"))
            : '<iconify-icon icon="lucide:sliders-horizontal" style="font-size:16px"></iconify-icon> ' + escape(_t("Choose Options"));

        overlay.classList.add("open");
        lockScroll(true);
        overlay.querySelector("#qv-close")?.focus();
    },

    _closeQuickView() {
        const overlay = this.el.querySelector("#qv-overlay");
        if (overlay?.classList.contains("open")) {
            overlay.classList.remove("open");
            lockScroll(false);
        }
    },

    _onQuickViewOverlayClick(ev) {
        if (ev.target === ev.currentTarget) {
            this._closeQuickView();
        }
    },

    async _onQuickViewAdd(ev) {
        const btn = ev.currentTarget;
        if (!btn.dataset.productId) {
            if (btn.dataset.url) {
                window.location.href = btn.dataset.url;
            }
            return;
        }
        btn.disabled = true;
        try {
            await this._addToCart(btn.dataset.productId);
            flashAdded(btn, '<iconify-icon icon="lucide:check" style="font-size:16px"></iconify-icon> ' + escape(_t("Added!")), 1600, "#22C55E");
        } catch {
            this._showToast(_t("Could not add this product to your cart."), true);
        } finally {
            btn.disabled = false;
        }
    },

    // newsletter -----------------------------------------------------------

    async _onNewsletterSubmit(ev) {
        ev.preventDefault();
        const form = ev.currentTarget;
        const input = form.querySelector("input[name=email]");
        const btn = form.querySelector("button[type=submit]");
        btn.disabled = true;
        try {
            const res = await rpc("/petzen/newsletter", { email: input.value });
            if (res.success) {
                form.reset();
                this._showToast(_t("Thanks for subscribing! 🐾"));
            } else {
                this._showToast(res.error, true);
            }
        } catch {
            this._showToast(_t("Network error. Please try again."), true);
        } finally {
            btn.disabled = false;
        }
    },

    // service booking ------------------------------------------------------

    async _onBookingSubmit(ev) {
        ev.preventDefault();
        const form = ev.currentTarget;
        const btn = form.querySelector(".booking-submit");
        const val = (name) => (form.querySelector(`[name="${name}"]`)?.value || "").trim();
        btn.disabled = true;
        try {
            const res = await rpc("/services/book", {
                pet_name: val("pet-name"),
                pet_type: val("pet-type"),
                service: val("service"),
                owner_name: val("owner-name"),
                email: val("email"),
                phone: val("phone"),
                date: val("preferred-date"),
                notes: val("notes"),
            });
            if (!res.success) {
                this._showToast(res.error, true);
                return;
            }
            btn.textContent = _t("✓ Booking Confirmed! We'll contact you shortly.");
            btn.style.background = "#22C55E";
            setTimeout(() => {
                form.reset();
                btn.textContent = _t("Book Appointment");
                btn.style.background = "";
            }, 3000);
        } catch {
            this._showToast(_t("Network error. Please try again."), true);
        } finally {
            btn.disabled = false;
        }
    },
});

// ── Products section: tabs, carousel, category filters ──────────────────────
// Base of the Petzen Products snippet widget (products_snippet.js), not registered.

export const PetzenProducts = publicWidget.Widget.extend({
    events: {
        "click .tab-pill": "_onTabClick",
        "click .c-prev": "_onPrev",
        "click .c-next": "_onNext",
        "mouseenter": "_stopAuto",
        "mouseleave": "_startAuto",
        "focusin": "_stopAuto",
        "focusout": "_startAuto",
    },
    DELAY: 3500,

    start() {
        this.row = this.el.querySelector(".products-row");
        this.outer = this.el.querySelector(".carousel-outer");
        this.dots = this.el.querySelector(".c-dots");
        this.idx = 0;
        this._onResize = this._onResize.bind(this);
        window.addEventListener("resize", this._onResize, { passive: true });
        this._rebuild();
        return this._super(...arguments);
    },

    destroy() {
        this._stopAuto();
        window.removeEventListener("resize", this._onResize);
        if (this.row) {
            this.row.style.transform = "";
        }
        this._super(...arguments);
    },

    // filters ------------------------------------------------------------

    _filter(key) {
        const pills = [...this.el.querySelectorAll(".tab-pill")];
        const match = pills.find((p) => p.dataset.f === key) || pills.find((p) => p.dataset.f === "all");
        pills.forEach((p) => p.classList.toggle("active", p === match));
        const f = match ? match.dataset.f : "all";
        this.row?.querySelectorAll(".product-card").forEach((card) => {
            card.style.display = f === "all" || card.dataset.cat === f ? "" : "none";
            card.classList.add("in"); // cards shown by a filter must not stay hidden by the reveal
        });
        this.idx = 0;
        this._rebuild();
    },

    _onTabClick(ev) {
        this._filter(ev.currentTarget.dataset.f);
    },

    // carousel -----------------------------------------------------------

    _cards() {
        return [...(this.row?.querySelectorAll(".product-card") || [])].filter((c) => c.style.display !== "none");
    },

    _step() {
        const card = this._cards()[0];
        if (!card) {
            return 0;
        }
        const gap = parseFloat(getComputedStyle(this.row).columnGap) || 24;
        return card.offsetWidth + gap;
    },

    _visible() {
        const step = this._step();
        return step && this.outer ? Math.max(1, Math.round((this.outer.clientWidth + 24) / step)) : 4;
    },

    _maxIdx() {
        return Math.max(0, this._cards().length - this._visible());
    },

    _rebuild() {
        if (!this.row) {
            return;
        }
        if (this.dots) {
            this.dots.innerHTML = "";
            const pages = this._maxIdx() + 1;
            for (let i = 0; i < pages; i++) {
                const dot = document.createElement("button");
                dot.type = "button";
                dot.className = "c-dot" + (i === 0 ? " active" : "");
                dot.setAttribute("aria-label", _t("Go to slide %s", i + 1));
                dot.addEventListener("click", () => {
                    this.idx = i;
                    this._update();
                    this._startAuto();
                });
                this.dots.appendChild(dot);
            }
        }
        this._update();
        this._startAuto();
    },

    _update() {
        const max = this._maxIdx();
        this.idx = Math.min(Math.max(this.idx, 0), max);
        this.row.style.transform = `translateX(-${this.idx * this._step()}px)`;
        const prev = this.el.querySelector(".c-prev");
        const next = this.el.querySelector(".c-next");
        if (prev) {
            prev.disabled = this.idx <= 0;
        }
        if (next) {
            next.disabled = this.idx >= max;
        }
        this.dots?.querySelectorAll(".c-dot").forEach((dot, i) => {
            dot.classList.remove("active");
            if (i === this.idx) {
                void dot.offsetWidth; // restart the progress animation
                dot.classList.add("active");
            }
        });
    },

    _onPrev() {
        this.idx--;
        this._update();
        this._startAuto();
    },

    _onNext() {
        this.idx++;
        this._update();
        this._startAuto();
    },

    _onResize() {
        this._rebuild();
    },

    _startAuto() {
        this._stopAuto();
        if (this.editableMode || this._maxIdx() < 1) {
            return;
        }
        this.timer = setInterval(() => {
            this.idx = this.idx >= this._maxIdx() ? 0 : this.idx + 1;
            this._update();
        }, this.DELAY);
    },

    _stopAuto() {
        clearInterval(this.timer);
        this.timer = null;
    },
});
