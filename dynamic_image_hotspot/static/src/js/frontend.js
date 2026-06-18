/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

/**
 * Public widget that renders hotspot markers on the visitor-facing website.
 * State is persisted on the <img> via data-attributes:
 *   data-hotspot="on"          — feature is active
 *   data-hotspot-x="<0-100>"  — horizontal position (%)
 *   data-hotspot-y="<0-100>"  — vertical position (%)
 *   data-hotspot-product-id   — linked product.template id
 */
publicWidget.registry.ImageHotspot = publicWidget.Widget.extend({
    selector: "img[data-hotspot='on']",

    start() {
        this._super(...arguments);
        this._renderHotspot();
    },

    _renderHotspot() {
        const imgEl = this.el;
        imgEl.parentElement.style.position = "relative";

        // Avoid duplicate markers on re-mount
        const existing = imgEl.nextElementSibling;
        if (existing?.classList.contains("popup-product")) {
            existing.remove();
        }

        const x  = parseFloat(imgEl.dataset.hotspotX)         || 50;
        const y  = parseFloat(imgEl.dataset.hotspotY)         || 50;
        const pid = imgEl.dataset.hotspotProductId;

        const anchor = imgEl.ownerDocument.createElement("a");
        anchor.className  = "popup-product";
        anchor.style.left = `${x}%`;
        anchor.style.top  = `${y}%`;

        if (pid) {
            anchor.setAttribute("href", `/shop/${pid}`);
        }

        imgEl.after(anchor);
    },
});
