/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

/**
 * Product Information Showcase Widget.
 * Handles tab switching for product details and manages visual states for
 * product attribute selections like colors and badges.
 */
publicWidget.registry.ProductInfoShowcase = publicWidget.Widget.extend({
    selector: ".section-tab",
    events: {
        "click .nav-link": "_onTabClick",
        "click .color-attr-select": "_onAttributeSelect",
        "click .badge-attr-select": "_onAttributeSelect",
    },
    /**
     * Handles tab switching logic.
     * @private
     * @param {Event} ev
     */
    _onTabClick: function (ev) {
        const target = ev.currentTarget;
        const tabId = target.getAttribute("data-bs-target");
        if (!tabId) {
            return;
        }
        const $target = $(target);
        $target.closest(".nav-tabs").find(".nav-link").removeClass("active").attr("aria-selected", "false");
        $target.addClass("active").attr("aria-selected", "true");
        const $tabContent = $target.closest(".section-tab").find(".tab-content-babycare");
        $tabContent.find(".tab-pane").removeClass("show active");
        $tabContent.find(tabId).addClass("show active");
    },
    /**
     * Manages visual feedback for attribute selection (colors, sizes, etc.).
     * @private
     * @param {Event} ev
     */
    _onAttributeSelect: function (ev) {
        const $target = $(ev.currentTarget);
        const isColor = $target.hasClass('color-attr-select');
        // Clear active sibling states
        if (isColor) {
            $target.siblings().removeClass('active');
            $target.addClass('active');
        } else {
            $target.siblings().removeClass('bg-dark text-white active').addClass('text-dark');
            $target.addClass('bg-dark text-white active').removeClass('text-dark');
        }
        // Note: In a full implementation, we would also update the hidden product_id input 
        // by matching the combination of selected attributes to a specific variant.
    },
});
