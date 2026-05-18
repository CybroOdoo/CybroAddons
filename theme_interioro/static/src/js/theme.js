/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";


function initScroll({ el, containerSel, itemSel, speed, animName }) {
    const track = el.querySelector(containerSel);
    if (!track) return null;

    track.querySelectorAll("[data-dup]").forEach(n => n.remove());
    track.style.animation = "";

    const reals = Array.from(track.querySelectorAll(`${itemSel}:not([data-dup])`));
    if (!reals.length) return null;

    reals.forEach(item => {
        const clone = item.cloneNode(true);
        clone.dataset.dup = "1";
        clone.setAttribute("aria-hidden", "true");
        clone.querySelectorAll(".o_editable, .o_we_custom_image")
             .forEach(e => e.classList.remove("o_editable", "o_we_custom_image"));
        track.appendChild(clone);
    });

    void track.offsetWidth;

    requestAnimationFrame(() => {
        const first = track.querySelector(itemSel);
        if (!first) return;
        const totalPx = reals.length * first.getBoundingClientRect().width;
        const dur = Math.max(5, Math.round(totalPx / speed));
        track.style.animation = `${animName} ${dur}s linear infinite`;
    });

    return track;
}

// ── Mobile Menu ───────────────────────────────────────────────────────────────
publicWidget.registry.InterioroMobileMenu = publicWidget.Widget.extend({
    selector: ".header",
    disabledInEditableMode: true,

    start() {
        this._super(...arguments);
        const toggle = document.getElementById("mobileToggle");
        const close  = document.getElementById("mobileClose");
        const menu   = document.getElementById("mobileMenu");

        if (toggle && menu) {
            const open = () => {
                menu.classList.add("active");
                toggle.classList.add("active");
                document.body.classList.add("menu-open");
            };
            const shut = () => {
                menu.classList.remove("active");
                toggle.classList.remove("active");
                document.body.classList.remove("menu-open");
            };

            toggle.addEventListener("click", open);
            if (close) close.addEventListener("click", shut);
            this.el.querySelectorAll(".mobile-nav a").forEach(a => a.addEventListener("click", shut));
            document.addEventListener("keydown", e => e.key === "Escape" && shut());
        }

        window.addEventListener("scroll", () => {
            this.el.classList.toggle("scrolled", window.scrollY > 10);
        }, { passive: true });

        return Promise.resolve();
    },
});

// ── Products Carousel ─────────────────────────────────────────────────────────
publicWidget.registry.InterioroProductsCarousel = publicWidget.Widget.extend({
    selector: ".ipc-section",
    disabledInEditableMode: true,

    start() {
        this._super(...arguments);
        this._track = initScroll({
            el: this.el,
            containerSel: ".ipc-reel",
            itemSel: ".ipc-card",
            speed: 90,
            animName: "ipc-slide",
        });
        return Promise.resolve();
    },

    destroy() {
        if (this._track) {
            this._track.querySelectorAll("[data-dup]").forEach(n => n.remove());
            this._track.style.animation = "";
        }
        this._super(...arguments);
    },
});

// ── Brand Logo Strip ──────────────────────────────────────────────────────────
publicWidget.registry.InterioroBrandStrip = publicWidget.Widget.extend({
    selector: ".interioro-brand-strip",
    disabledInEditableMode: true,

    start() {
        this._super(...arguments);
        this._track = initScroll({
            el: this.el,
            containerSel: ".ibs-track",
            itemSel: ".ibs-logo",
            speed: 45,
            animName: "ibs-scroll",
        });
        return Promise.resolve();
    },

    destroy() {
        if (this._track) {
            this._track.querySelectorAll("[data-dup]").forEach(n => n.remove());
            this._track.style.animation = "";
        }
        this._super(...arguments);
    },
});

// ── FAQ Accordion ─────────────────────────────────────────────────────────────
publicWidget.registry.InterioroFaq = publicWidget.Widget.extend({
    selector: ".itr-faq",
    events: { "click .itr-faq-q": "_onToggle" },

    _onToggle(ev) {
        const item = ev.currentTarget.closest(".itr-faq-item");
        const wasActive = item.classList.contains("active");
        this.el.querySelectorAll(".itr-faq-item.active").forEach(i => i.classList.remove("active"));
        if (!wasActive) item.classList.add("active");
    },
});
