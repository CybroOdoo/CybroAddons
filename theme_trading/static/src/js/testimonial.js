/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.TestimonialCarousel = publicWidget.Widget.extend({
    selector: ".o_testimonial_snippet",

    start() {
        this._super(...arguments);

        const carousel = this.el.querySelector(".js_testimonial_carousel");
        if (!carousel) {
            return;
        }

        // Generate unique ID
        const uniqueId = `testimonial_carousel_${Date.now()}_${Math.floor(Math.random() * 1000)}`;

        carousel.id = uniqueId;

        // Update control buttons
        const prevBtn = this.el.querySelector(".js-carousel-prev");
        const nextBtn = this.el.querySelector(".js-carousel-next");

        if (prevBtn) {
            prevBtn.setAttribute("data-bs-target", `#${uniqueId}`);
        }
        if (nextBtn) {
            nextBtn.setAttribute("data-bs-target", `#${uniqueId}`);
        }
    },
});
