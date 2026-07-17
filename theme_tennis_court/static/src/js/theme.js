/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

/**
 * Mobile menu widget for Tennis Court theme.
 * Handles opening/closing of the mobile sidebar and scroll effects.
 */
publicWidget.registry.TcMobileMenu = publicWidget.Widget.extend({
    selector: ".tc-header",
    disabledInEditableMode: true,
    /**
     * @override
     */
    start() {
        this._super(...arguments);
        const toggle = document.getElementById("tc_mobile_toggle");
        const close = document.getElementById("tc_mobile_close");
        const menu = document.getElementById("tc_mobile_menu");
        const overlay = document.getElementById("tc_mobile_overlay");
        if (toggle && menu) {
            const open = () => {
                menu.classList.add("active");
                if (overlay) overlay.classList.add("active");
                document.body.classList.add("tc-menu-open");
            };
            const shut = () => {
                menu.classList.remove("active");
                if (overlay) overlay.classList.remove("active");
                document.body.classList.remove("tc-menu-open");
            };
            toggle.addEventListener("click", open);
            if (close) close.addEventListener("click", shut);
            if (overlay) overlay.addEventListener("click", shut);
            // Close on nav link click
            this.el.querySelectorAll(".tc-mobile-nav a")
                .forEach(a => a.addEventListener("click", shut));
            // Close on Escape key
            document.addEventListener("keydown", e => {
                if (e.key === "Escape") shut();
            });
        }
        // Scroll effect — add 'scrolled' class to header
        window.addEventListener("scroll", () => {
            this.el.classList.toggle("scrolled", window.scrollY > 10);
        }, { passive: true });
        return Promise.resolve();
    },
});
/**
 * Tournament filter widget for Tennis Court theme.
 * Allows filtering tournament cards based on category tabs.
 */
publicWidget.registry.TcTourFilter = publicWidget.Widget.extend({
    selector: ".tc-tour-section",
    disabledInEditableMode: true,
    events: {
        "click .filter-tab": "_onTabClick",
    },
    /**
     * @override
     */
    start() {
        return this._super(...arguments);
    },
    /**
     * Handles the click on a filter tab.
     *
     * @private
     * @param {MouseEvent} ev
     */
    _onTabClick(ev) {
        const tab = ev.currentTarget;
        this.el.querySelectorAll(".filter-tab").forEach(t => t.classList.remove("active"));
        tab.classList.add("active");
        const filter = tab.getAttribute("data-filter");
        this.el.querySelectorAll(".tour-card").forEach(card => {
            if (filter === "all" || card.getAttribute("data-category") === filter) {
                card.style.display = "flex";
            } else {
                card.style.display = "none";
            }
        });
    }
});
