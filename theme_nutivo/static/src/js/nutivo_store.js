/**
 * Nutivo storefront.
 *
 * Bag and wishlist drawers, product quick view, pack size selection and
 * toasts of the Nutivo design.
 * The bag is the website cart and the wishlist the eCommerce wishlist: every
 * change goes through the standard eCommerce routes, the theme controller
 * only renders the panels.
 */
import { markup } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";
import { registry } from "@web/core/registry";
import { setElementContent } from "@web/core/utils/html";
import { Interaction } from "@web/public/interaction";
import wishlistUtils from "@website_sale/js/wishlist_utils";
import wSaleUtils from "@website_sale/js/website_sale_utils";

const TOAST_DURATION = 4000;
const MAX_TOASTS = 3;
const FOCUSABLE = 'a[href], button:not([disabled]), input:not([disabled]):not([type="hidden"]), select, textarea, [tabindex="0"]';

export class NutivoStore extends Interaction {
    static selector = ".nv-wrap";

    setup() {
        this.body = this.el.ownerDocument.body;
        this.scrim = this.el.querySelector(".nv-scrim");
        this.toastStack = this.el.querySelector(".nv-toast-stack");
        this.activePanel = null;
        this.lastFocus = null;
        this.qvQty = 1;
    }

    start() {
        this.addListener(this.el, "click", this.onClick);
        this.addListener(this.el, "keydown", this.onKeydown);
        this.syncCartBadges();
        this.registerCleanup(() => this.body.classList.remove("nv-no-scroll"));
    }

    // ---------------------------------------------------------------------
    // Header
    // ---------------------------------------------------------------------

    /**
     * The page cache only refreshes the first cart badge: copy it to the
     * other badges (bottom navigation).
     */
    syncCartBadges() {
        const [first, ...others] = this.el.querySelectorAll(".my_cart_quantity");
        if (!first) {
            return;
        }
        for (const badge of others) {
            badge.textContent = first.textContent;
            badge.classList.toggle("d-none", first.classList.contains("d-none"));
        }
    }

    // ---------------------------------------------------------------------
    // Panels: drawers and quick view
    // ---------------------------------------------------------------------

    getPanel(name) {
        return this.el.querySelector(`[data-panel="${name}"]`);
    }

    /**
     * @param {string} name cart, wishlist or quickview
     */
    openPanel(name) {
        const panel = this.getPanel(name);
        if (!panel) {
            return;
        }
        if (this.activePanel && this.activePanel !== panel) {
            this.closePanel(false);
        }
        this.lastFocus = this.el.ownerDocument.activeElement;
        this.activePanel = panel;
        panel.classList.add("nv-is-open");
        panel.setAttribute("aria-hidden", "false");
        this.body.classList.add("nv-no-scroll");
        if (this.scrim) {
            this.scrim.hidden = false;
            this.waitForAnimationFrame(() => this.scrim.classList.add("nv-is-visible"));
        }
        if (name === "cart") {
            this.renderBag();
        } else if (name === "wishlist") {
            this.renderWishlist();
        }
        this.waitForTimeout(() => {
            const target =
                panel.querySelector('input:not([type="hidden"]):not([type="checkbox"])') ||
                panel.querySelector("[data-close]");
            target?.focus();
        }, 80);
    }

    closePanel(restore = true) {
        if (!this.activePanel) {
            return;
        }
        this.activePanel.classList.remove("nv-is-open");
        this.activePanel.setAttribute("aria-hidden", "true");
        this.activePanel = null;
        this.body.classList.remove("nv-no-scroll");
        if (this.scrim) {
            this.scrim.classList.remove("nv-is-visible");
            this.waitForTimeout(() => {
                if (!this.activePanel) {
                    this.scrim.hidden = true;
                }
            }, 350);
        }
        if (restore) {
            this.lastFocus?.focus?.();
        }
    }

    /**
     * Keep the keyboard focus inside the open dialog.
     *
     * @param {KeyboardEvent} ev
     */
    trapFocus(ev) {
        const container = this.activePanel;
        if (!container || ev.key !== "Tab") {
            return;
        }
        const focusables = [...container.querySelectorAll(FOCUSABLE)].filter(
            (el) => el.offsetParent !== null
        );
        if (!focusables.length) {
            return;
        }
        const first = focusables[0];
        const last = focusables[focusables.length - 1];
        const active = this.el.ownerDocument.activeElement;
        if (ev.shiftKey && active === first) {
            ev.preventDefault();
            last.focus();
        } else if (!ev.shiftKey && active === last) {
            ev.preventDefault();
            first.focus();
        }
    }

    // ---------------------------------------------------------------------
    // Events
    // ---------------------------------------------------------------------

    onKeydown(ev) {
        if (ev.key === "Escape") {
            this.closePanel();
            return;
        }
        this.trapFocus(ev);
        const sizeBtn = ev.target.closest?.("[data-size]");
        if (sizeBtn && ["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"].includes(ev.key)) {
            ev.preventDefault();
            const group = [...sizeBtn.parentElement.querySelectorAll("[data-size]:not([disabled])")];
            const dir = ev.key === "ArrowLeft" || ev.key === "ArrowUp" ? -1 : 1;
            const next = group[(group.indexOf(sizeBtn) + dir + group.length) % group.length];
            this.selectSize(next);
            next.focus();
        }
    }

    onClick(ev) {
        const target = ev.target;
        const opener = target.closest("[data-open]");
        if (opener) {
            ev.preventDefault();
            this.openPanel(opener.dataset.open);
            return;
        }
        if (target.closest("[data-close]") || target === this.scrim) {
            this.closePanel();
            return;
        }
        const sizeBtn = target.closest("[data-size]");
        if (sizeBtn) {
            this.selectSize(sizeBtn);
            return;
        }
        const addonCheck = target.closest("[data-addon-check]");
        if (addonCheck) {
            addonCheck.closest(".nv-addon").querySelector(".nv-addon__opts").hidden =
                !addonCheck.checked;
            return;
        }
        const addonBtn = target.closest("[data-addon-size], [data-addon-extra]");
        if (addonBtn) {
            this.selectAddonOption(addonBtn);
            return;
        }
        const extraBtn = target.closest("[data-extra]");
        if (extraBtn) {
            this.selectExtra(extraBtn);
            return;
        }
        const wishBtn = target.closest("[data-wish]");
        if (wishBtn) {
            wishBtn.classList.remove("nv-pop");
            void wishBtn.offsetWidth;
            wishBtn.classList.add("nv-pop");
            this.toggleWish(wishBtn);
            return;
        }
        const quick = target.closest("[data-quick]");
        if (quick) {
            this.openQuickView(quick.dataset.quick);
            return;
        }
        const qvStep = target.closest("[data-qv-step]");
        if (qvStep) {
            this.stepQuickView(Number(qvStep.dataset.qvStep));
            return;
        }
        const addBtn = target.closest("[data-add]");
        if (addBtn) {
            this.onAdd(addBtn);
            return;
        }
        const promoOpen = target.closest("[data-promo-open]");
        if (promoOpen) {
            const form = promoOpen.parentElement.querySelector(".nv-promo__form");
            promoOpen.hidden = true;
            form.hidden = false;
            form.querySelector('input[name="promo"]').focus();
            return;
        }
        if (target.closest("[data-move-all]")) {
            this.moveAllToBag();
            return;
        }
        const moveBtn = target.closest("[data-move-to-bag]");
        if (moveBtn) {
            this.moveToBag(moveBtn);
            return;
        }
        const line = target.closest(".nv-bag-item[data-line-id]");
        if (line) {
            const qtyBtn = target.closest(".nv-qty__btn[data-qty]");
            if (qtyBtn) {
                this.updateLine(line, Number(line.dataset.lineQty) + Number(qtyBtn.dataset.qty));
            } else if (target.closest("[data-remove]")) {
                this.updateLine(line, 0);
            }
            return;
        }
    }

    // ---------------------------------------------------------------------
    // Pack sizes
    // ---------------------------------------------------------------------

    /**
     * Select a pack size on every rendering of the product.
     *
     * @param {HTMLElement} btn the `[data-size]` button
     */
    selectSize(btn) {
        const card = btn.closest("[data-product]");
        if (!card) {
            return;
        }
        const index = btn.dataset.size;
        for (const other of this.el.querySelectorAll(`[data-product="${card.dataset.product}"]`)) {
            const sizes = other.querySelectorAll("[data-size]");
            if (!sizes.length) {
                continue;
            }
            for (const size of sizes) {
                const on = size.dataset.size === index;
                size.setAttribute("aria-checked", on);
                size.tabIndex = on ? 0 : -1;
                if (on) {
                    other.dataset.productId = size.dataset.productId;
                    const priceEl = other.querySelector("[data-price]");
                    if (priceEl) {
                        priceEl.textContent = size.dataset.sizePrice;
                    }
                }
            }
            this.refreshCustom(other);
        }
    }

    /**
     * Select a value of an option that does not make a variant (quick view).
     *
     * @param {HTMLElement} btn the `[data-extra]` button
     */
    selectExtra(btn) {
        for (const other of btn.parentElement.querySelectorAll("[data-extra]")) {
            other.setAttribute("aria-checked", other === btn);
        }
        this.refreshCustom(btn.closest("[data-product]"));
    }

    /**
     * Select a variant or an option of an optional product (quick view).
     *
     * @param {HTMLElement} btn the `[data-addon-size]` or `[data-addon-extra]` button
     */
    selectAddonOption(btn) {
        const kind = btn.hasAttribute("data-addon-size") ? "data-addon-size" : "data-addon-extra";
        for (const other of btn.parentElement.querySelectorAll(`[${kind}]`)) {
            other.setAttribute("aria-checked", other === btn);
        }
        const addon = btn.closest(".nv-addon");
        if (kind === "data-addon-size") {
            addon.dataset.addonProductId = btn.dataset.addonSize;
            addon.querySelector("[data-addon-price]").textContent = btn.dataset.sizePrice;
        }
    }

    /**
     * The optional products ticked in the quick view, as the cart route wants them.
     *
     * @param {HTMLElement} card element holding the product data
     * @returns {Object[]}
     */
    linkedProductsOf(card) {
        return [...card.querySelectorAll(".nv-addon")]
            .filter((addon) => addon.querySelector("[data-addon-check]").checked)
            .map((addon) => ({
                product_template_id: parseInt(addon.dataset.addon),
                product_id: parseInt(addon.dataset.addonProductId),
                parent_product_template_id: parseInt(card.dataset.product),
                quantity: 1,
                product_custom_attribute_values: [],
                no_variant_attribute_value_ids: [
                    ...addon.querySelectorAll('[data-addon-extra][aria-checked="true"]'),
                ].map((el) => parseInt(el.dataset.addonExtra)),
            }));
    }

    /**
     * The custom text field shows while a chosen option asks for one.
     *
     * @param {HTMLElement} card element holding the product data
     */
    refreshCustom(card) {
        const field = card.querySelector(".nv-quickview__custom");
        if (!field) {
            return;
        }
        const needed = card.querySelector(
            '[data-custom][aria-checked="true"]:not([data-custom=""])'
        );
        field.hidden = !needed;
    }

    /**
     * What the quick view adds to the product: the values of the options that
     * do not make a variant and the custom text.
     *
     * @param {HTMLElement} card element holding the product data
     * @returns {Object|null} extra parameters, null when a custom text is missing
     */
    optionsOf(card) {
        const params = {};
        const extras = [...card.querySelectorAll('[data-extra][aria-checked="true"]')];
        if (extras.length) {
            params.no_variant_attribute_value_ids = extras.map((el) => parseInt(el.dataset.extra));
        }
        const field = card.querySelector("[data-qv-custom]");
        if (field && !field.closest("[hidden]")) {
            const text = field.value.trim();
            if (!text) {
                field.focus();
                this.toast({ title: "Please enter your custom text", icon: "x", tone: "neutral" });
                return null;
            }
            const ids = [...card.querySelectorAll('[data-custom][aria-checked="true"]')]
                .flatMap((el) => el.dataset.custom.split(" ").filter(Boolean))
                .map((id) => parseInt(id));
            params.product_custom_attribute_values = [...new Set(ids)].map((id) => ({
                custom_product_template_attribute_value_id: id,
                custom_value: text,
            }));
        }
        const linked = this.linkedProductsOf(card);
        if (linked.length) {
            params.linked_products = linked;
        }
        return params;
    }

    // ---------------------------------------------------------------------
    // Bag
    // ---------------------------------------------------------------------

    async onAdd(btn) {
        const card = btn.closest("[data-product-id]");
        if (!card) {
            return;
        }
        const quantity = btn.hasAttribute("data-qv-add") ? this.qvQty : 1;
        const options = btn.hasAttribute("data-qv-add") ? this.optionsOf(card) : {};
        if (!options) {
            return;
        }
        const added = await this.addToCart(card, quantity, false, options);
        if (!added) {
            return;
        }
        btn.classList.add("nv-is-added");
        this.waitForTimeout(() => btn.classList.remove("nv-is-added"), 1200);
        if (btn.hasAttribute("data-qv-add")) {
            this.closePanel();
        }
    }

    /**
     * Add the selected variant of a card to the cart.
     *
     * @param {HTMLElement} card element holding the product data
     * @param {number} quantity
     * @param {boolean} silent do not show a toast
     * @param {Object} options extra parameters of the cart route
     * @returns {Promise<boolean>} whether the product was added
     */
    async addToCart(card, quantity = 1, silent = false, options = {}) {
        const data = await this.waitFor(
            rpc("/shop/cart/add", {
                product_template_id: parseInt(card.dataset.product),
                product_id: parseInt(card.dataset.productId),
                quantity,
                ...options,
            })
        );
        wSaleUtils.updateCartNavBar(data);
        const warning = (data.notifications || []).find((n) => n.type === "warning");
        if (warning) {
            this.toast({ title: warning.data.warning_message, icon: "x", tone: "neutral" });
        } else if (!silent) {
            const name = card.querySelector(
                ".nv-pcard__name, .o_wsale_products_item_title, .nv-hamper__name, .nv-mini__name, .nv-quickview__name, .nv-line-item__name"
            );
            const size = card.querySelector('[data-size][aria-checked="true"]');
            this.toast({
                title: `${name ? name.textContent.trim() : ""} added`,
                sub: size ? size.textContent.trim() : "",
                image: card.querySelector("img")?.getAttribute("src"),
                action: { label: "View bag", run: () => this.openPanel("cart") },
            });
        }
        if (this.activePanel === this.getPanel("cart")) {
            card.closest(".nv-mini")?.remove();
            await this.renderBag();
        }
        return !warning && Boolean(data.cart_quantity);
    }

    async updateLine(line, quantity) {
        const name = line.querySelector(".nv-bag-item__name")?.textContent.trim();
        const data = await this.waitFor(
            rpc("/shop/cart/update", {
                line_id: parseInt(line.dataset.lineId),
                quantity: Math.max(quantity, 0),
            })
        );
        wSaleUtils.updateCartNavBar(data);
        await this.renderBag();
        if (quantity <= 0) {
            this.toast({ title: `${name} removed`, icon: "x" });
        }
    }

    async renderBag() {
        const data = await this.waitFor(rpc("/theme_nutivo/bag"));
        const panel = this.getPanel("cart");
        const hadFocus = panel.contains(this.el.ownerDocument.activeElement);
        setElementContent(panel, markup(data.html));
        if (hadFocus) {
            panel.querySelector("[data-close]")?.focus();
        }
    }

    // ---------------------------------------------------------------------
    // Wishlist
    // ---------------------------------------------------------------------

    /**
     * @param {HTMLElement} btn the `[data-wish]` button
     */
    async toggleWish(btn) {
        const card = btn.closest("[data-product]");
        const result = await this.waitFor(
            rpc("/theme_nutivo/wishlist/toggle", { product_id: parseInt(btn.dataset.wish) })
        );
        this.syncWishlist(result.product_ids);
        if (card) {
            this.paintHearts(card.dataset.product, result.on);
        }
        const name = card?.querySelector(
            ".nv-pcard__name, .nv-hamper__name, .nv-quickview__name, .nv-line-item__name"
        );
        this.toast({
            title: result.on ? "Saved to wishlist" : "Removed from wishlist",
            sub: name ? name.textContent.trim() : "",
            image: result.on ? card?.querySelector("img")?.getAttribute("src") : null,
            icon: result.on ? null : "heart",
        });
        if (this.activePanel === this.getPanel("wishlist")) {
            this.renderWishlist();
        }
    }

    paintHearts(productTemplateId, on) {
        for (const card of this.el.querySelectorAll(`[data-product="${productTemplateId}"]`)) {
            const heart = card.querySelector(".nv-wish-btn");
            if (!heart) {
                continue;
            }
            heart.setAttribute("aria-pressed", on);
            const icon = heart.querySelector(".nv-i");
            icon.classList.toggle("nv-ph-heart-fill", on);
            icon.classList.toggle("nv-ph-heart-light", !on);
        }
    }

    syncWishlist(productIds) {
        wishlistUtils.setWishlistProductIds(productIds);
        wishlistUtils.updateWishlistNavBar();
    }

    async renderWishlist() {
        const data = await this.waitFor(rpc("/theme_nutivo/wishlist"));
        this.syncWishlist(data.product_ids);
        setElementContent(this.el.querySelector("[data-wish-items]"), markup(data.html));
    }

    async moveToBag(btn) {
        const item = btn.closest("[data-product-id]");
        const added = await this.addToCart(item);
        if (!added) {
            return;
        }
        const result = await this.waitFor(
            rpc("/theme_nutivo/wishlist/toggle", { product_id: parseInt(btn.dataset.moveToBag) })
        );
        this.syncWishlist(result.product_ids);
        this.paintHearts(item.dataset.product, false);
        this.renderWishlist();
    }

    async moveAllToBag() {
        const items = [...this.el.querySelectorAll("[data-wish-items] .nv-line-item")];
        for (const item of items) {
            await this.addToCart(item, 1, true);
            const result = await this.waitFor(
                rpc("/theme_nutivo/wishlist/toggle", { product_id: parseInt(item.dataset.productId) })
            );
            this.syncWishlist(result.product_ids);
            this.paintHearts(item.dataset.product, false);
        }
        await this.renderWishlist();
        const count = items.length;
        this.toast({
            title: `${count} ${count === 1 ? "item" : "items"} moved to your bag`,
            icon: "handbag",
            action: { label: "View bag", run: () => this.openPanel("cart") },
        });
    }

    // ---------------------------------------------------------------------
    // Quick view
    // ---------------------------------------------------------------------

    async openQuickView(productTemplateId) {
        const html = await this.waitFor(
            rpc("/theme_nutivo/quick_view", { product_template_id: parseInt(productTemplateId) })
        );
        if (!html) {
            return;
        }
        this.qvQty = 1;
        const body = this.el.querySelector(".nv-quickview__body");
        setElementContent(body, markup(html));
        const card = body.querySelector("[data-product]");
        if (card) {
            this.refreshCustom(card);
        }
        this.openPanel("quickview");
    }

    stepQuickView(step) {
        const body = this.el.querySelector(".nv-quickview__body");
        this.qvQty = Math.min(20, Math.max(1, this.qvQty + step));
        body.querySelector("[data-qv-qty]").textContent = this.qvQty;
        body.querySelector('[data-qv-step="-1"]').disabled = this.qvQty <= 1;
        body.querySelector('[data-qv-step="1"]').disabled = this.qvQty >= 20;
    }

    // ---------------------------------------------------------------------
    // Feedback
    // ---------------------------------------------------------------------

    /**
     * Show a toast; hovering it pauses the timer.
     *
     * @param {Object} params
     * @param {string} params.title
     * @param {string} [params.sub]
     * @param {string} [params.image] thumbnail url
     * @param {Object} [params.action] {label, run}
     * @param {string} [params.icon] Phosphor icon name, without the -light suffix
     * @param {string} [params.tone] success, neutral or info
     */
    toast({ title, sub, image, action, icon, tone }) {
        if (!this.toastStack) {
            return;
        }
        const doc = this.el.ownerDocument;
        const autoTone =
            /removed|cancelled/i.test(title) || icon === "x"
                ? "neutral"
                : icon === "check" || image
                ? "success"
                : "info";
        const el = doc.createElement("div");
        el.className = `nv-toast nv-toast--${tone || autoTone}`;
        el.setAttribute("role", "status");
        el.style.setProperty("--nv-toast-time", `${TOAST_DURATION}ms`);
        const makeIcon = (name) => {
            const i = doc.createElement("i");
            i.className = `nv-i nv-ph-${name}-light`;
            i.setAttribute("aria-hidden", "true");
            return i;
        };
        if (image) {
            const img = doc.createElement("img");
            img.className = "nv-toast__thumb";
            img.src = image;
            img.alt = "";
            el.append(img);
        } else {
            const span = doc.createElement("span");
            span.className = "nv-toast__icon";
            span.append(makeIcon(icon || "check"));
            el.append(span);
        }
        const body = doc.createElement("p");
        body.className = "nv-toast__body";
        const strong = doc.createElement("strong");
        strong.textContent = title;
        body.append(strong);
        if (sub) {
            const small = doc.createElement("small");
            small.textContent = sub;
            body.append(small);
        }
        el.append(body);
        let timer = null;
        let left = TOAST_DURATION;
        let started = Date.now();
        const dismiss = () => {
            clearTimeout(timer);
            el.classList.add("nv-is-leaving");
            setTimeout(() => el.remove(), 300);
        };
        if (action) {
            const actionBtn = doc.createElement("button");
            actionBtn.type = "button";
            actionBtn.className = "nv-toast__action";
            actionBtn.textContent = action.label;
            actionBtn.addEventListener("click", () => {
                action.run();
                dismiss();
            });
            el.append(actionBtn);
        }
        const close = doc.createElement("button");
        close.type = "button";
        close.className = "nv-toast__close";
        close.setAttribute("aria-label", "Dismiss notification");
        close.append(makeIcon("x"));
        close.addEventListener("click", dismiss);
        const timerBar = doc.createElement("span");
        timerBar.className = "nv-toast__timer";
        timerBar.setAttribute("aria-hidden", "true");
        el.append(close, timerBar);
        el.addEventListener("mouseenter", () => {
            clearTimeout(timer);
            left -= Date.now() - started;
            el.classList.add("nv-is-paused");
        });
        el.addEventListener("mouseleave", () => {
            started = Date.now();
            timer = setTimeout(dismiss, Math.max(800, left));
            el.classList.remove("nv-is-paused");
        });
        this.toastStack.append(el);
        while (this.toastStack.children.length > MAX_TOASTS) {
            this.toastStack.firstElementChild.remove();
        }
        timer = setTimeout(dismiss, left);
    }
}

registry.category("public.interactions").add("theme_nutivo.store", NutivoStore);
