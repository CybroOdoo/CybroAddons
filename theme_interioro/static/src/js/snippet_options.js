/** @odoo-module **/

/**
 * Custom snippet options for the Interioro theme.
 * This module defines options for brand strips and product carousels.
 */
import options from "@web_editor/js/editor/snippets.options";
/**
 * Option registry for the Interioro Brand Strip snippet.
 */
options.registry.interioro_brand_strip = options.Class.extend({
    /**
     * Adds a new brand logo to the strip by cloning the last existing logo.
     *
     * @param {string} previewMode
     * @param {any} widgetValue
     * @param {Object} params
     */
    addBrandLogo(previewMode, widgetValue, params) {
        const track = this.$target[0].querySelector(".ibs-track");
        if (!track) return;
        const logos = Array.from(track.querySelectorAll(".ibs-logo:not([data-dup])"));
        if (!logos.length) return;
        track.appendChild(logos[logos.length - 1].cloneNode(true));
    },
    /**
     * Removes the last brand logo from the strip, ensuring at least one remains.
     *
     * @param {string} previewMode
     * @param {any} widgetValue
     * @param {Object} params
     */
    removeBrandLogo(previewMode, widgetValue, params) {
        const track = this.$target[0].querySelector(".ibs-track");
        if (!track) return;
        const logos = Array.from(track.querySelectorAll(".ibs-logo:not([data-dup])"));
        if (logos.length <= 1) return;
        logos[logos.length - 1].remove();
    },
});
/**
 * Option registry for the Interioro Products Carousel snippet.
 */
options.registry.interioro_products_carousel = options.Class.extend({
    /**
     * Adds a new product card to the carousel by cloning the last existing card.
     *
     * @param {string} previewMode
     * @param {any} widgetValue
     * @param {Object} params
     */
    addProductCard(previewMode, widgetValue, params) {
        const reel = this.$target[0].querySelector(".ipc-reel");
        if (!reel) return;
        const cards = Array.from(reel.querySelectorAll(".ipc-card:not([data-dup])"));
        if (!cards.length) return;
        const copy = cards[cards.length - 1].cloneNode(true);
        reel.appendChild(copy);
    },
    /**
     * Removes the last product card from the carousel, ensuring at least one remains.
     *
     * @param {string} previewMode
     * @param {any} widgetValue
     * @param {Object} params
     */
    removeProductCard(previewMode, widgetValue, params) {
        const reel = this.$target[0].querySelector(".ipc-reel");
        if (!reel) return;
        const cards = Array.from(reel.querySelectorAll(".ipc-card:not([data-dup])"));
        if (cards.length <= 1) return;
        cards[cards.length - 1].remove();
    },
});
