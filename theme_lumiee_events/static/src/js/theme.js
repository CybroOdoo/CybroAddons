/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

/**
 * Mobile Menu Widget
 * Handles the hamburger toggle, drawer menu, and header scroll effects.
 */
publicWidget.registry.LeMobileMenu = publicWidget.Widget.extend({
    selector: "#leMainHeader",
    disabledInEditableMode: true,
    /**
     * @override
     */
    start() {
        this._super(...arguments);
        const toggle = this.el.querySelector("#leMobileToggle");
        const menu = this.el.querySelector("#leMobileMenu");
        const close = this.el.querySelector("#leMobileClose");
        const overlay = this.el.querySelector("#leMobileOverlay");
        const openMenu = () => {
            if (menu) menu.classList.add("active");
            if (overlay) overlay.classList.add("active");
            document.body.classList.add("le-menu-open");
        };
        const closeMenu = () => {
            if (menu) menu.classList.remove("active");
            if (overlay) overlay.classList.remove("active");
            document.body.classList.remove("le-menu-open");
        };
        if (toggle) toggle.addEventListener("click", openMenu);
        if (close) close.addEventListener("click", closeMenu);
        if (overlay) overlay.addEventListener("click", closeMenu);
        // Close on nav link click
        if (menu) {
            menu.querySelectorAll("a").forEach(a => {
                a.addEventListener("click", closeMenu);
            });
        }
        // Scroll effect — add 'scrolled' class to header
        window.addEventListener("scroll", () => {
            this.el.classList.toggle("scrolled", window.scrollY > 50);
        }, { passive: true });
        // Active nav link — highlight current page
        const currentPath = window.location.pathname;
        this.el.querySelectorAll(".le-nav-menu ul li a, .le-mobile-nav ul li a").forEach(link => {
            const href = link.getAttribute("href");
            if (href === currentPath || (href === "/" && currentPath === "/") ||
                (href !== "/" && currentPath.startsWith(href))) {
                link.classList.add("le-nav-active");
            }
        });
        return Promise.resolve();
    },
});
/**
 * FAQ Accordion Widget
 * Handles the toggling of FAQ questions to show/hide answers.
 */
publicWidget.registry.LeFaqAccordion = publicWidget.Widget.extend({
    selector: ".le-faq-section",
    disabledInEditableMode: true,
    events: {
        "click .le-faq-question": "_onToggle",
    },
    /**
     * Toggles the active state of an FAQ item.
     * @private
     * @param {Event} ev
     */
    _onToggle(ev) {
        const item = ev.currentTarget.closest(".le-faq-item");
        if (!item) return;
        const wasActive = item.classList.contains("active");
        this.el.querySelectorAll(".le-faq-item").forEach(i => i.classList.remove("active"));
        if (!wasActive) item.classList.add("active");
    },
});
/**
 * Gallery Filter Widget
 * Handles filtering of gallery items based on category buttons.
 */
publicWidget.registry.LeGalleryFilter = publicWidget.Widget.extend({
    selector: ".le-gallery-filter-section",
    disabledInEditableMode: true,
    events: {
        "click .le-filter-btn": "_onFilter",
    },
    /**
     * Filters gallery items by category.
     * @private
     * @param {Event} ev
     */
    _onFilter(ev) {
        const btn = ev.currentTarget;
        const filter = btn.dataset.filter;
        this.el.querySelectorAll(".le-filter-btn").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        this.el.querySelectorAll(".le-gallery-grid .le-gallery-item").forEach(item => {
            if (filter === "all" || item.dataset.category === filter) {
                item.style.display = "block";
            } else {
                item.style.display = "none";
            }
        });
    },
});
/**
 * Contact Form Widget
 * Ensures the contact form is submitted correctly.
 */
publicWidget.registry.LeContactForm = publicWidget.Widget.extend({
    selector: "form[action='/website/form/']",
    disabledInEditableMode: true,
    events: {
        "click .le-submit-btn": "_onSubmit",
    },
    /**
     * Handles the submit button click.
     * @private
     * @param {Event} ev
     */
    _onSubmit(ev) {
        ev.preventDefault();
        this.el.submit();
    },
});
