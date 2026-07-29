/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.ThemeCordage = publicWidget.Widget.extend(/**
 * @lends publicWidget.registry.ThemeCordage.prototype
 */ {
    selector: "#wrapwrap",
    events: {
        "click [data-cordage-filter-target]": "_onProductFilterClick",
        "click .tc-pdp-tab-btn": "_onPdpTabClick",
        "click .o_product_page_reviews_link": "_onPdpReviewsLinkClick",
        "click .theme-cordage-ct-faq-q": "_onFaqClick",
    },

    /**
     * Lifecycle hook called once the widget's root element is ready in the DOM.
     * Runs the initial product-tab filter pass so the correct tab is active
     * on first render, then delegates to the parent `start` implementation.
     *
     * @returns {Promise} Result of the parent `_super` call, which Odoo's
     *   widget system awaits before marking the widget as started.
     */
    start() {
        this._initializeProductTabs();
        return this._super(...arguments);
    },

    /**
     * Scans the widget's root element for every product-tab group
     * (`[data-cordage-product-tabs]`) and applies the default "all" filter
     * to each group so that all product cards are visible on page load.
     *
     * If a group's first filter button carries a specific
     * `data-cordage-filter-target` value, that value is used instead of "all".
     *
     * @returns {void}
     */
    _initializeProductTabs() {
        const groups = this.el.querySelectorAll("[data-cordage-product-tabs]");
        for (const group of groups) {
            const firstButton = group.querySelector("[data-cordage-filter-target]");
            if (firstButton) {
                this._applyProductFilter(group, firstButton.dataset.cordageFilterTarget || "all");
            }
        }
    },

    /**
     * Applies a category filter to a product-tab group by toggling the active
     * state on filter buttons and showing or hiding product cards.
     *
     * A card is shown when `target` equals `"all"` or when the card's
     * space-separated `data-category-ids` attribute contains the `target` string.
     *
     * @param {Element} group - The tab-group container element that holds the
     *   filter buttons and references the product grid via its
     *   `data-cordage-product-tabs` attribute value (a CSS selector).
     * @param {string} target - The category identifier to filter by, or `"all"`
     *   to display every product card.
     * @returns {void}
     */
    _applyProductFilter(group, target) {
        const selector = group.getAttribute("data-cordage-product-tabs");
        const grid = selector ? document.querySelector(selector) : null;
        if (!grid) {
            return;
        }
        const buttons = group.querySelectorAll("[data-cordage-filter-target]");
        const cards = grid.querySelectorAll("[data-cordage-product-card]");

        for (const button of buttons) {
            button.classList.toggle("is-active", button.dataset.cordageFilterTarget === target);
        }
        for (const card of cards) {
            const categories = card.getAttribute("data-category-ids") || "";
            card.hidden = target !== "all" && !categories.split(" ").includes(target);
        }
    },

    /**
     * Handles click events on product-category filter buttons
     * (`[data-cordage-filter-target]`).
     *
     * Resolves the closest tab group ancestor and delegates to
     * `_applyProductFilter` with the clicked button's target value.
     *
     * @param {MouseEvent} ev - The click event. `ev.currentTarget` is the
     *   filter button element that was clicked.
     * @returns {void}
     */
    _onProductFilterClick(ev) {
        const button = ev.currentTarget;
        const group = button.closest("[data-cordage-product-tabs]");
        if (!group) {
            return;
        }
        this._applyProductFilter(group, button.dataset.cordageFilterTarget || "all");
    },

    /**
     * Handles click events on Product Detail Page (PDP) custom tab buttons
     * (`.tc-pdp-tab-btn`).
     *
     * Marks the clicked button as active, deactivates all sibling buttons,
     * and toggles the matching `.tc-pdp-tab-pane` element (matched by
     * `id === "tab-" + tabName`) within the same `.tc-pdp-tabs-section`
     * ancestor.
     *
     * @param {MouseEvent} ev - The click event. `ev.currentTarget` is the
     *   tab button element that was clicked. The button must carry a
     *   `data-tab` attribute whose value identifies the target pane.
     * @returns {void}
     */
    _onPdpTabClick(ev) {
        const btn = ev.currentTarget;
        const tabName = btn.dataset.tab;
        const parent = btn.closest(".tc-pdp-tabs-section");
        if (!parent) return;

        // Toggle active button
        const buttons = parent.querySelectorAll(".tc-pdp-tab-btn");
        for (const b of buttons) {
            b.classList.toggle("active", b === btn);
        }

        // Toggle active pane
        const panes = parent.querySelectorAll(".tc-pdp-tab-pane");
        for (const pane of panes) {
            pane.classList.toggle("active", pane.id === `tab-${tabName}`);
        }
    },

    /**
     * Handles click events on the PDP "Reviews" anchor link
     * (`.o_product_page_reviews_link`).
     *
     * Prevents the default anchor navigation, programmatically activates the
     * "reviews" tab in the PDP tab section, and smoothly scrolls the tab
     * section into view.
     *
     * @param {MouseEvent} ev - The click event on the reviews anchor link.
     * @returns {void}
     */
    _onPdpReviewsLinkClick(ev) {
        ev.preventDefault();
        const tabsSection = this.el.querySelector(".tc-pdp-tabs-section");
        if (!tabsSection) return;

        const reviewsBtn = tabsSection.querySelector('.tc-pdp-tab-btn[data-tab="reviews"]');
        if (reviewsBtn) {
            reviewsBtn.click();
        }
        tabsSection.scrollIntoView({ behavior: "smooth" });
    },

    /**
     * Handles click events on Contact-Us page FAQ question buttons
     * (`.theme-cordage-ct-faq-q`).
     *
     * Implements an accordion behaviour: all currently open FAQ items are
     * collapsed, then the clicked item is toggled open (unless it was already
     * open, in which case it stays closed).
     *
     * The open state is conveyed via the `"is-open"` CSS class on both the
     * `.theme-cordage-ct-faq-item` wrapper and the sibling
     * `.theme-cordage-ct-faq-a` answer element.
     *
     * @param {MouseEvent} ev - The click event. `ev.currentTarget` is the
     *   question button (`.theme-cordage-ct-faq-q`) that was clicked.
     * @returns {void}
     */
    _onFaqClick(ev) {
        const btn = ev.currentTarget;
        const item = btn.closest(".theme-cordage-ct-faq-item");
        const answer = item ? item.querySelector(".theme-cordage-ct-faq-a") : null;
        if (!item || !answer) return;

        const isOpen = item.classList.contains("is-open");

        // Close all other items
        const allItems = this.el.querySelectorAll(".theme-cordage-ct-faq-item");
        for (const otherItem of allItems) {
            otherItem.classList.remove("is-open");
            const otherAnswer = otherItem.querySelector(".theme-cordage-ct-faq-a");
            if (otherAnswer) {
                otherAnswer.classList.remove("is-open");
            }
        }

        // Toggle current item
        if (!isOpen) {
            item.classList.add("is-open");
            answer.classList.add("is-open");
        }
    },
});
