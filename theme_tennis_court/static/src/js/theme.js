/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";


// ── Mobile Menu ───────────────────────────────────────────────────────
publicWidget.registry.TcMobileMenu = publicWidget.Widget.extend({
    selector: ".tc-header",
    disabledInEditableMode: true,

    start() {
        this._super(...arguments);

        const toggle  = document.getElementById("tcMobileToggle");
        const close   = document.getElementById("tcMobileClose");
        const menu    = document.getElementById("tcMobileMenu");
        const overlay = document.getElementById("tcMobileOverlay");

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

// ── Tour Filter ───────────────────────────────────────────────────────
publicWidget.registry.TcTourFilter = publicWidget.Widget.extend({
    selector: ".tc-tour-section",
    disabledInEditableMode: true,
    events: {
        "click .filter-tab": "_onTabClick",
    },

    start() {
        return this._super(...arguments);
    },

    _onTabClick(ev) {
        const tab = ev.currentTarget;
        this.el.querySelectorAll(".filter-tab")
            .forEach(t => t.classList.remove("active"));
        tab.classList.add("active");
        
        const filter = tab.getAttribute("data-filter");
        this.el.querySelectorAll(".tour-card").forEach(card => {
            const isMatch = filter === "all" ||
                card.getAttribute("data-category") === filter;
            if (isMatch) {
                card.style.display = "flex";
            } else {
                card.style.display = "none";
            }
        });
    }
});
