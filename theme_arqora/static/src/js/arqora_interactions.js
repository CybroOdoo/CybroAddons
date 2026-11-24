/**
 * Arqora interactions.
 *
 * The motion layer (header height, split headings, reveals, count-up figures,
 * words that light up while reading, the drawing that draws on), the dimmable
 * hero room, the light levels by space, the accordion and the home blocks
 * filled with the shop categories and products. Everything is reverted when
 * an interaction stops, so the edit mode only saves the markup of the blocks.
 */
import { markup } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";
import { registry } from "@web/core/registry";
import { setElementContent } from "@web/core/utils/html";
import { Interaction } from "@web/public/interaction";

const prefersReducedMotion = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const VISIBLE = "aq-is-visible";

/**
 * Page motion: keeps the header height variable up to date and reveals the
 * blocks of the design while they enter the screen.
 */
export class ArqoraMotion extends Interaction {
    static selector = ".aq-wrap";

    setup() {
        this.doc = this.el.ownerDocument;
        this.html = this.doc.documentElement;
        this.splits = [];
        this.words = [];
        this.drawing = [];
    }

    start() {
        this.registerCleanup(() => this.revert());
        this.header = this.el.querySelector("header#top");
        this.syncHeader();
        if (this.header && window.ResizeObserver) {
            this.resizeObserver = new ResizeObserver(() => this.syncHeader());
            this.resizeObserver.observe(this.header);
        }
        this.addListener(window, "scroll", this.syncHeader, { passive: true });
        this.splitHeadings();
        this.prepareReadingText();
        this.html.classList.add("aq-is-loaded");
        this.observeReveals();
        if (this.words.length) {
            this.addListener(window, "scroll", this.updateReadingText, { passive: true });
            this.updateReadingText();
        }
    }

    /** Publish the live height of the header, 0 while it is hidden. */
    syncHeader() {
        const header = this.header;
        if (!header) {
            return;
        }
        const hidden = header.classList.contains("o_header_affixed") && header.getBoundingClientRect().bottom <= 0;
        const height = hidden ? 0 : header.getBoundingClientRect().height || header.offsetHeight;
        this.html.style.setProperty("--aq-header-h", `${Math.round(header.querySelector(".navbar")?.offsetHeight || height)}px`);
        this.html.style.setProperty("--aq-sticky-top", `${Math.max(0, Math.round(header.getBoundingClientRect().bottom))}px`);
    }

    /** Wrap each line of a split heading (lines are separated by `<br>`). */
    splitHeadings() {
        for (const heading of this.el.querySelectorAll("[data-split]")) {
            const original = heading.innerHTML;
            const lines = original.split(/<br\s*\/?>/i);
            heading.innerHTML = lines.map((line) => `<span class="aq-line"><span>${line}</span></span>`).join("");
            this.splits.push([heading, original]);
        }
    }

    /** Split the reading paragraph in words so they can light up. */
    prepareReadingText() {
        for (const text of this.el.querySelectorAll(".aq-litext")) {
            const original = text.innerHTML;
            const nodes = (text.textContent || "").trim().split(/\s+/).map((word) => {
                const span = this.doc.createElement("span");
                span.textContent = word;
                return span;
            });
            text.replaceChildren(...nodes.flatMap((span) => [span, this.doc.createTextNode(" ")]));
            this.words.push({ text, original, spans: nodes });
        }
    }

    updateReadingText() {
        const reduce = prefersReducedMotion();
        for (const { text, spans } of this.words) {
            let count = spans.length;
            if (!reduce) {
                const rect = text.getBoundingClientRect();
                const vh = window.innerHeight;
                const progress = Math.min(1, Math.max(0, (vh * 0.85 - rect.top) / (rect.height + vh * 0.35)));
                count = Math.round(progress * spans.length);
            }
            spans.forEach((span, i) => span.classList.toggle("aq-is-lit", i < count));
        }
    }

    observeReveals() {
        const targets = this.el.querySelectorAll("[data-reveal], [data-stagger], [data-split], .aq-drawing, [data-count]");
        if (!("IntersectionObserver" in window) || prefersReducedMotion()) {
            for (const el of targets) {
                this.reveal(el);
            }
            return;
        }
        this.io = new IntersectionObserver(
            (entries) => {
                for (const entry of entries) {
                    if (entry.isIntersecting) {
                        this.reveal(entry.target);
                        this.io.unobserve(entry.target);
                    }
                }
            },
            { threshold: 0.12, rootMargin: "0px 0px -6% 0px" }
        );
        for (const el of targets) {
            this.io.observe(el);
        }
    }

    reveal(el) {
        el.classList.add(VISIBLE);
        if (el.matches(".aq-drawing")) {
            el.classList.add("aq-is-drawn");
        }
        if (el.dataset.count) {
            this.countUp(el);
        }
    }

    countUp(el) {
        const end = parseFloat(el.dataset.count);
        if (prefersReducedMotion() || Number.isNaN(end)) {
            return;
        }
        const start = performance.now();
        const tick = (now) => {
            const t = Math.min(1, (now - start) / 1800);
            el.textContent = Math.round(end * (1 - Math.pow(1 - t, 4))).toLocaleString("en-GB");
            if (t < 1 && !this.stopped) {
                requestAnimationFrame(tick);
            }
        };
        requestAnimationFrame(tick);
    }

    revert() {
        this.stopped = true;
        this.io?.disconnect();
        this.resizeObserver?.disconnect();
        for (const [heading, original] of this.splits) {
            heading.innerHTML = original;
        }
        for (const { text, original } of this.words) {
            text.innerHTML = original;
        }
        for (const el of this.el.querySelectorAll(`.${VISIBLE}, .aq-is-drawn`)) {
            el.classList.remove(VISIBLE, "aq-is-drawn");
        }
        this.html.classList.remove("aq-is-loaded");
    }
}

/**
 * Hero room: the visitor lights the room with the mouse, the dimmer and the
 * switch. A light drifts over the room while nothing is touched.
 */
export class ArqoraHero extends Interaction {
    static selector = ".s_arqora_hero";

    setup() {
        this.room = this.el.querySelector(".aq-dim__room");
        this.dimmer = this.el.querySelector(".aq-dimmer input");
        this.output = this.el.querySelector(".aq-dimmer output");
        this.switch = this.el.querySelector(".aq-dim__switch");
        this.hint = this.el.querySelector(".aq-dim__hint");
        this.pos = { x: 50, y: 30 };
        this.target = { x: 50, y: 30 };
        this.touched = false;
        this.raf = null;
        this.t0 = performance.now();
    }

    start() {
        if (!this.room || !this.dimmer) {
            return;
        }
        this.reduce = prefersReducedMotion();
        this.addListener(this.el, "pointermove", (ev) => {
            if (!ev.target.closest(".aq-dim__bar")) {
                this.move(ev.clientX, ev.clientY);
            }
        });
        this.addListener(this.el, "pointerdown", (ev) => {
            if (!ev.target.closest("a, button, input")) {
                this.move(ev.clientX, ev.clientY);
            }
        });
        this.addListener(this.dimmer, "input", () => this.setDim(+this.dimmer.value));
        this.addListener(this.switch, "click", this.toggle);
        this.setDim(+this.dimmer.value);
        if (this.reduce) {
            this.paint();
        } else {
            this.raf = requestAnimationFrame((now) => this.loop(now));
            this.io = new IntersectionObserver((entries) => {
                if (entries[0].isIntersecting) {
                    this.raf = this.raf || requestAnimationFrame((now) => this.loop(now));
                } else {
                    cancelAnimationFrame(this.raf);
                    this.raf = null;
                }
            });
            this.io.observe(this.el);
        }
        this.registerCleanup(() => {
            cancelAnimationFrame(this.raf);
            this.raf = null;
            this.io?.disconnect();
            for (const name of ["--aq-x", "--aq-y", "--aq-dim"]) {
                this.el.style.removeProperty(name);
            }
            this.el.classList.remove("aq-is-on");
            this.hint?.classList.remove("aq-is-gone");
        });
    }

    setDim(value) {
        this.el.style.setProperty("--aq-dim", value / 100);
        this.output.textContent = `${Math.round(value)}%`;
        const on = value >= 95;
        this.el.classList.toggle("aq-is-on", on);
        this.switch.setAttribute("aria-pressed", on);
        this.switch.querySelector("span").textContent = on ? this.env_label_off : this.env_label_on;
    }

    get env_label_on() {
        return this.switch.dataset.labelOn || "Lights on";
    }

    get env_label_off() {
        return this.switch.dataset.labelOff || "Lights off";
    }

    paint() {
        this.pos.x += (this.target.x - this.pos.x) * 0.12;
        this.pos.y += (this.target.y - this.pos.y) * 0.12;
        this.el.style.setProperty("--aq-x", `${this.pos.x.toFixed(2)}%`);
        this.el.style.setProperty("--aq-y", `${this.pos.y.toFixed(2)}%`);
    }

    loop(now) {
        if (!this.touched && !this.reduce) {
            const t = (now - this.t0) / 1000;
            this.target.x = 50 + Math.sin(t * 0.4) * 20;
            this.target.y = 34 + Math.cos(t * 0.55) * 14;
        }
        this.paint();
        this.raf = requestAnimationFrame((time) => this.loop(time));
    }

    move(clientX, clientY) {
        const rect = this.room.getBoundingClientRect();
        this.target.x = ((clientX - rect.left) / rect.width) * 100;
        this.target.y = ((clientY - rect.top) / rect.height) * 100;
        if (!this.touched) {
            this.touched = true;
            this.hint?.classList.add("aq-is-gone");
        }
    }

    toggle() {
        const to = this.el.classList.contains("aq-is-on") ? 18 : 100;
        const from = +this.dimmer.value;
        const start = performance.now();
        const step = (now) => {
            const k = Math.min(1, (now - start) / 700);
            const value = from + (to - from) * (1 - Math.pow(1 - k, 3));
            this.dimmer.value = value;
            this.setDim(value);
            if (k < 1 && this.raf !== undefined) {
                requestAnimationFrame(step);
            }
        };
        requestAnimationFrame(step);
    }
}

/** Light levels by space: tabs, pictures and the lux meter card. */
export class ArqoraSpaces extends Interaction {
    static selector = ".s_arqora_spaces";

    setup() {
        this.tabs = [...this.el.querySelectorAll(".aq-rooms__tab")];
        this.images = [...this.el.querySelectorAll(".aq-rooms__img img")];
        this.card = this.el.querySelector(".aq-rooms__card");
    }

    start() {
        const list = this.el.querySelector(".aq-rooms__tabs");
        if (!list || !this.card) {
            return;
        }
        this.addListener(list, "click", (ev) => {
            const tab = ev.target.closest(".aq-rooms__tab");
            if (tab) {
                this.show(this.tabs.indexOf(tab));
            }
        });
        this.addListener(list, "keydown", (ev) => {
            if (ev.key !== "ArrowRight" && ev.key !== "ArrowLeft") {
                return;
            }
            const index = this.tabs.indexOf(this.el.ownerDocument.activeElement);
            if (index < 0) {
                return;
            }
            const next = (index + (ev.key === "ArrowRight" ? 1 : -1) + this.tabs.length) % this.tabs.length;
            this.tabs[next].focus();
            this.show(next);
        });
        this.show(0);
    }

    show(index) {
        const tab = this.tabs[index];
        if (!tab) {
            return;
        }
        this.tabs.forEach((el, i) => {
            el.classList.toggle("aq-is-active", i === index);
            el.setAttribute("aria-selected", i === index);
        });
        this.images.forEach((img, i) => img.classList.toggle("aq-is-active", i === index));
        const set = (selector, text) => {
            const node = this.card.querySelector(selector);
            if (node) {
                node.textContent = text;
            }
        };
        set("[data-aq-no]", String(index + 1).padStart(2, "0"));
        set("[data-aq-name]", tab.dataset.name);
        set("[data-aq-lux]", tab.dataset.lux);
        set("[data-aq-cct]", tab.dataset.cct);
        set("[data-aq-rule]", tab.dataset.rule);
        this.card.querySelector("[data-aq-scale] i")?.style.setProperty("--aq-v", `${(tab.dataset.lux / 600) * 100}%`);
    }
}

/** Accordion of the FAQ: one panel opens at a time. */
export class ArqoraAccordion extends Interaction {
    static selector = ".aq-accordion";
    dynamicContent = {
        ".aq-accordion__btn": { "t-on-click": this.onToggle },
    };

    onToggle(ev) {
        const item = ev.currentTarget.closest(".aq-accordion__item");
        const open = !item.classList.contains("aq-is-open");
        for (const other of this.el.querySelectorAll(".aq-accordion__item")) {
            other.classList.remove("aq-is-open");
            other.querySelector(".aq-accordion__btn")?.setAttribute("aria-expanded", "false");
        }
        if (open) {
            item.classList.add("aq-is-open");
            item.querySelector(".aq-accordion__btn")?.setAttribute("aria-expanded", "true");
        }
    }
}

/**
 * Home blocks filled with the shop: the lamp tiles come from the published
 * categories, the Objects of Light mosaic from the first published products.
 */
export class ArqoraShopBlock extends Interaction {
    static selector = "[data-aq-collections], [data-aq-signature]";

    async willStart() {
        const isCollections = "aqCollections" in this.el.dataset;
        const route = isCollections ? "/theme_arqora/collections" : "/theme_arqora/signature";
        const result = await this.waitFor(rpc(route, { limit: parseInt(this.el.dataset.limit) || undefined }));
        this.html = result.html;
    }

    start() {
        if (this.html) {
            setElementContent(this.el, markup(this.html));
        }
        // No hover on touch screens: the tile nearest the centre switches on.
        if (this.el.matches("[data-aq-collections]") && !window.matchMedia("(hover: hover)").matches && "IntersectionObserver" in window) {
            this.io = new IntersectionObserver(
                (entries) => entries.forEach((entry) => entry.target.classList.toggle("aq-is-on", entry.isIntersecting)),
                { rootMargin: "-42% 0px -42% 0px" }
            );
            this.el.querySelectorAll(".aq-lamp").forEach((lamp) => this.io.observe(lamp));
        }
        this.registerCleanup(() => {
            this.io?.disconnect();
            this.el.replaceChildren();
        });
    }
}

/**
 * Shop grid: tiles rise in as they enter the viewport, the way the reference
 * catalogue reveals its product cards (staggered per row).
 */
export class ArqoraShopMotion extends Interaction {
    static selector = "#products_grid";

    setup() {
        this.reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    }

    start() {
        if (this.reduced || !("IntersectionObserver" in window)) {
            return;
        }
        const tiles = [...this.el.querySelectorAll(".oe_product")];
        this.io = new IntersectionObserver(
            (entries) => {
                for (const entry of entries) {
                    if (entry.isIntersecting) {
                        entry.target.classList.add("aq-in");
                        this.io.unobserve(entry.target);
                    }
                }
            },
            { threshold: 0.12, rootMargin: "0px 0px -6% 0px" }
        );
        tiles.forEach((tile, i) => {
            tile.classList.add("aq-reveal-tile");
            tile.style.setProperty("--aq-delay", `${(i % 3) * 0.08}s`);
            this.io.observe(tile);
        });
        this.registerCleanup(() => {
            this.io.disconnect();
            tiles.forEach((tile) => {
                tile.classList.remove("aq-reveal-tile", "aq-in");
                tile.style.removeProperty("--aq-delay");
            });
        });
    }
}

/**
 * Parallax: any element carrying data-aq-parallax="<speed>" drifts against
 * the scroll, as [data-parallax] does in the reference.
 */
export class ArqoraParallax extends Interaction {
    static selector = "[data-aq-parallax]";
    dynamicContent = {
        _window: { "t-on-scroll": this.update, "t-on-resize": this.update },
    };

    setup() {
        this.reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    }

    start() {
        this.update();
        this.registerCleanup(() => {
            this.el.style.transform = "";
        });
    }

    update() {
        if (this.reduced) {
            return;
        }
        const box = this.el.parentElement.getBoundingClientRect();
        const vh = window.innerHeight;
        if (box.bottom < -100 || box.top > vh + 100) {
            return;
        }
        const speed = parseFloat(this.el.dataset.aqParallax) || 0.12;
        const offset = (box.top + box.height / 2 - vh / 2) * -speed;
        this.el.style.transform = `translate3d(0, ${offset.toFixed(1)}px, 0)`;
    }
}

/**
 * Contact page: the audience tabs set the "I am a" field of the standard
 * website form, the intro line and the company label.
 */
export class ArqoraEnquiry extends Interaction {
    static selector = ".aq-contact__form";
    dynamicContent = {
        ".aq-enquiry-tab": { "t-on-click": this.onTab },
    };

    async willStart() {
        // A Request a Quote link carries the product to quote:
        // /contactus?type=architect&product=12&finish=Brushed+brass
        this.params = new URLSearchParams(window.location.search);
        const id = parseInt(this.params.get("product"), 10);
        this.product = id ? await this.waitFor(rpc("/theme_arqora/quote_product", { product_id: id })) : null;
    }

    start() {
        const tab = this.el.querySelector(`.aq-enquiry-tab[data-aq-key='${this.params.get("type")}']`);
        if (tab) {
            this.selectTab(tab);
        }
        const finish = this.params.get("finish") || "";
        const message = [];
        if (this.product && this.product.name) {
            this.showProduct(this.product, finish);
            message.push(
                `I would like to request a quotation for the ${this.product.name}${finish ? ` in ${finish}` : ""}.`
            );
        }
        if (this.params.get("topic") === "samples") {
            message.push(
                `Please send finish samples${finish ? ` of ${finish}` : ""} to our studio.`
            );
        }
        if (message.length) {
            // The website form fills its own fields while it starts: write
            // the starting message once it is done.
            this.waitForTimeout(() => {
                const textarea = this.el.querySelector("textarea[name='description']");
                if (textarea && !textarea.value) {
                    textarea.value = message.join(" ");
                }
            }, 400);
        }
        this.registerCleanup(() => this.hideProduct());
    }

    /** Show the card of the product and send its name with the enquiry. */
    showProduct(product, finish) {
        const card = this.el.querySelector(".aq-product-ref");
        const input = this.el.querySelector("input[name='product']");
        if (input) {
            input.value = finish ? `${product.name} (${finish})` : product.name;
        }
        if (!card) {
            return;
        }
        card.querySelector(".aq-product-ref__image").src = product.image;
        card.querySelector(".aq-product-ref__name").textContent = product.name;
        card.querySelector(".aq-product-ref__meta").textContent = [finish, product.price && `From ${product.price}`]
            .filter(Boolean)
            .join(" · ");
        card.hidden = false;
    }

    hideProduct() {
        const card = this.el.querySelector(".aq-product-ref");
        if (card) {
            card.hidden = true;
        }
    }

    onTab(ev) {
        this.selectTab(ev.currentTarget);
    }

    selectTab(tab) {
        this.el.querySelectorAll(".aq-enquiry-tab").forEach((t) => {
            const on = t === tab;
            t.classList.toggle("is-active", on);
            t.setAttribute("aria-selected", on);
        });
        const intro = this.el.querySelector(".aq-enquiry-intro");
        if (intro) {
            intro.textContent = tab.dataset.aqIntro;
        }
        const select = this.el.querySelector("select[name='name']");
        if (select) {
            select.value = tab.dataset.aqType;
            select.dispatchEvent(new Event("change", { bubbles: true }));
        }
        const label = this.el.querySelector("label[for='aq_contact_company'] .s_website_form_label_content");
        if (label) {
            label.textContent = tab.dataset.aqCompany;
        }
    }
}

/**
 * Product page of a quote-only product: the Request a Quotation link carries
 * the finish the visitor picks.
 */
export class ArqoraQuoteLink extends Interaction {
    static selector = ".aq-pdp-quote #product_details";
    dynamicContent = {
        ".js_variant_change": { "t-on-change": this.onChange },
    };

    start() {
        const button = this.el.querySelector("#quote-btn");
        this.baseHref = button?.getAttribute("href");
        this.onChange();
        this.registerCleanup(() => button?.setAttribute("href", this.baseHref));
        if (button) {
            // The standard product page adds a "subject" to the link of the
            // contact button, which would fill the enquiry type of the form
            // with the product name: take it out again.
            const observer = new MutationObserver(() => {
                const url = new URL(button.getAttribute("href"), window.location.origin);
                if (url.searchParams.has("subject")) {
                    url.searchParams.delete("subject");
                    button.setAttribute("href", url.pathname + url.search);
                }
            });
            observer.observe(button, { attributes: true, attributeFilter: ["href"] });
            this.registerCleanup(() => observer.disconnect());
        }
    }

    /** Put the names of the chosen attribute values in the link. */
    onChange() {
        const button = this.el.querySelector("#quote-btn");
        if (!button || !this.baseHref) {
            return;
        }
        const names = [];
        for (const input of this.el.querySelectorAll("input.js_variant_change:checked")) {
            names.push(
                input.dataset.valueName ||
                    input.dataset.value_name ||
                    input.closest("label")?.textContent.trim() ||
                    ""
            );
        }
        for (const select of this.el.querySelectorAll("select.js_variant_change")) {
            names.push(select.selectedOptions[0]?.textContent.trim() || "");
        }
        const url = new URL(this.baseHref, window.location.origin);
        const finish = names.filter(Boolean).join(" / ");
        if (finish) {
            url.searchParams.set("finish", finish);
        }
        button.setAttribute("href", url.pathname + url.search);
    }
}

/**
 * Desktop navbar: three links left, three right and every further menu in
 * the "+" dropdown. The menu stays whole on small screens, where the mobile
 * menu lists everything.
 */
export class ArqoraNavOverflow extends Interaction {
    static selector = "header#top:has(.aq-nav) #top_menu";
    // Home and Materials only show in the mobile menu, so the first eight
    // entries make the three plus three links.
    static VISIBLE_ITEMS = 8;

    setup() {
        this.mq = window.matchMedia("(min-width: 992px)");
        this.toggle = null;
    }

    start() {
        this.adapt();
        this.addListener(this.mq, "change", () => this.adapt());
        this.registerCleanup(() => this.restore());
    }

    restore() {
        if (!this.toggle) {
            return;
        }
        for (const item of [...this.toggle.querySelector(".dropdown-menu").children]) {
            item.classList.add("nav-item");
            item.classList.remove("dropdown-item");
            const link = item.querySelector(":scope > .dropdown-item");
            if (link) {
                link.classList.remove("dropdown-item");
                link.classList.add("nav-link");
            }
            this.el.insertBefore(item, this.toggle);
        }
        this.toggle.remove();
        this.toggle = null;
    }

    adapt() {
        this.restore();
        const items = [...this.el.children].filter((node) => node.matches("li.nav-item"));
        const extra = items.slice(this.constructor.VISIBLE_ITEMS);
        if (!this.mq.matches || !extra.length) {
            return;
        }
        const toggle = document.createElement("li");
        toggle.className = "nav-item dropdown o_extra_menu_items aq-nav-more";
        toggle.setAttribute("role", "presentation");
        toggle.innerHTML =
            '<a role="menuitem" href="#" class="nav-link dropdown-toggle o-no-caret" ' +
            'data-bs-toggle="dropdown" aria-expanded="false" aria-label="More">' +
            '<i class="oi" data-icon="add"></i></a><ul class="dropdown-menu"></ul>';
        const menu = toggle.querySelector(".dropdown-menu");
        this.el.insertBefore(toggle, extra[0]);
        for (const item of extra) {
            item.classList.remove("nav-item");
            item.classList.add("dropdown-item", "p-0");
            const link = item.querySelector(":scope > .nav-link");
            if (link) {
                link.classList.remove("nav-link");
                link.classList.add("dropdown-item");
            }
            menu.appendChild(item);
        }
        this.toggle = toggle;
    }
}

registry
    .category("public.interactions")
    .add("theme_arqora.motion", ArqoraMotion)
    .add("theme_arqora.hero", ArqoraHero)
    .add("theme_arqora.spaces", ArqoraSpaces)
    .add("theme_arqora.accordion", ArqoraAccordion)
    .add("theme_arqora.shop_block", ArqoraShopBlock)
    .add("theme_arqora.shop_motion", ArqoraShopMotion)
    .add("theme_arqora.parallax", ArqoraParallax)
    .add("theme_arqora.enquiry", ArqoraEnquiry)
    .add("theme_arqora.nav_overflow", ArqoraNavOverflow)
    .add("theme_arqora.quote_link", ArqoraQuoteLink);
