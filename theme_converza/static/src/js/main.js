/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

/**
 * Animates a number from 0 to its `data-count` value when it becomes visible.
 */
publicWidget.registry.CvzCounter = publicWidget.Widget.extend({
    selector: "[data-count]",

    start() {
        this.observer = new IntersectionObserver(
            (entries) => {
                for (const entry of entries) {
                    if (entry.isIntersecting) {
                        this._countUp();
                        this.observer.unobserve(entry.target);
                    }
                }
            },
            { threshold: 0.5 }
        );
        this.observer.observe(this.el);
        return this._super(...arguments);
    },

    destroy() {
        this.observer.disconnect();
        this._super(...arguments);
    },

    _countUp() {
        const el = this.el;
        const end = parseFloat(el.dataset.count);
        const suffix = el.dataset.suffix || "";
        const isFloat = el.dataset.count.includes(".");
        const duration = 1800;
        const start = performance.now();

        const animate = (now) => {
            const progress = Math.min((now - start) / duration, 1);
            const value = end * (1 - Math.pow(1 - progress, 3));
            el.textContent = (isFloat ? value.toFixed(1) : Math.round(value)) + suffix;
            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };
        requestAnimationFrame(animate);
    },
});

/**
 * Industry filter buttons of the case studies page.
 */
publicWidget.registry.CvzCaseFilter = publicWidget.Widget.extend({
    selector: ".case-filter-btn",
    events: {
        click: "_onClick",
    },

    _onClick(ev) {
        ev.preventDefault();
        const doc = this.el.ownerDocument;
        doc.querySelectorAll(".case-filter-btn").forEach((btn) => btn.classList.remove("active"));
        this.el.classList.add("active");

        // The target is the part after "#" in the href ("#b2b" -> "b2b").
        const href = this.el.getAttribute("href") || "";
        const targetId = href.includes("#") ? href.split("#")[1] : "";
        const showAll = targetId === "" || targetId === "all";

        doc.querySelectorAll(".case-card").forEach((card) => {
            card.style.display = showAll || card.id === targetId ? "block" : "none";
        });
    },
});

/**
 * Category filter buttons of the blog archive.
 */
publicWidget.registry.CvzBlogFilter = publicWidget.Widget.extend({
    selector: ".filter-bar .filter-btn",
    events: {
        click: "_onClick",
    },

    _onClick(ev) {
        ev.preventDefault();
        const doc = this.el.ownerDocument;
        doc.querySelectorAll(".filter-bar .filter-btn").forEach((btn) => btn.classList.remove("active"));
        this.el.classList.add("active");

        const filterValue = this.el.dataset.filter;
        doc.querySelectorAll(".blog-grid .blog-card").forEach((card) => {
            const visible = filterValue === "all" || card.dataset.category === filterValue;
            card.style.display = visible ? "block" : "none";
        });
    },
});

/**
 * Monthly / annual switch of the pricing page. The annual price is stored in
 * the `data-annual` attribute of each price, the monthly one in `data-monthly`.
 */
publicWidget.registry.CvzBillingToggle = publicWidget.Widget.extend({
    selector: ".billing-toggle-wrap",
    events: {
        "change #billing-toggle": "_onToggle",
    },

    _onToggle(ev) {
        const key = ev.currentTarget.checked ? "annual" : "monthly";
        const doc = this.el.ownerDocument;
        doc.querySelectorAll(".price-num[data-" + key + "]").forEach((price) => {
            price.textContent = price.dataset[key];
        });
    },
});
