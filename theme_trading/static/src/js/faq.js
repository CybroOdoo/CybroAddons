/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.FaqAccordion = publicWidget.Widget.extend({
    selector: ".o_faq_snippet",

    start() {
        this._super(...arguments);

        const accordion = this.el.querySelector(".js_faq_accordion");
        if (!accordion) return;

        const uid = `faq_${Date.now()}_${Math.floor(Math.random() * 1000)}`;
        accordion.id = uid;

        const toggles = accordion.querySelectorAll(".js-faq-toggle");
        const collapses = accordion.querySelectorAll(".js-faq-collapse");

        toggles.forEach((toggle, index) => {
            const collapse = collapses[index];
            if (!collapse) return;

            const collapseId = `${uid}_item_${index + 1}`;

            // Assign unique ID
            collapse.id = collapseId;

            // Wire toggle
            toggle.setAttribute("data-bs-target", `#${collapseId}`);
            toggle.setAttribute("aria-controls", collapseId);

            // Scope accordion
            collapse.setAttribute("data-bs-parent", `#${uid}`);
        });
    },
});
