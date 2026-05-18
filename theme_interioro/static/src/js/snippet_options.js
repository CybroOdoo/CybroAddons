/** @odoo-module **/

import options from "@web_editor/js/editor/snippets.options";

options.registry.interioro_brand_strip = options.Class.extend({
    addBrandLogo(previewMode, widgetValue, params) {
        const track = this.$target[0].querySelector(".ibs-track");
        if (!track) return;
        const logos = Array.from(track.querySelectorAll(".ibs-logo:not([data-dup])"));
        if (!logos.length) return;
        track.appendChild(logos[logos.length - 1].cloneNode(true));
    },
    removeBrandLogo(previewMode, widgetValue, params) {
        const track = this.$target[0].querySelector(".ibs-track");
        if (!track) return;
        const logos = Array.from(track.querySelectorAll(".ibs-logo:not([data-dup])"));
        if (logos.length <= 1) return;
        logos[logos.length - 1].remove();
    },
});

options.registry.interioro_products_carousel = options.Class.extend({
    addProductCard(previewMode, widgetValue, params) {
        const reel = this.$target[0].querySelector(".ipc-reel");
        if (!reel) return;
        const cards = Array.from(reel.querySelectorAll(".ipc-card:not([data-dup])"));
        if (!cards.length) return;
        const copy = cards[cards.length - 1].cloneNode(true);
        reel.appendChild(copy);
    },
    removeProductCard(previewMode, widgetValue, params) {
        const reel = this.$target[0].querySelector(".ipc-reel");
        if (!reel) return;
        const cards = Array.from(reel.querySelectorAll(".ipc-card:not([data-dup])"));
        if (cards.length <= 1) return;
        cards[cards.length - 1].remove();
    },
});
