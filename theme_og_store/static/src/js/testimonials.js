/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { renderToElement } from "@web/core/utils/render";

publicWidget.registry.Testimonial = publicWidget.Widget.extend({
    selector: ".testimonial_section",

    async start() {
        await this._super(...arguments);

        // Inject QWeb template
        this.el.innerHTML = "";
        this.el.appendChild(
            renderToElement("theme_og_store.testimonial_data")
        );

        this.testimonialBanner();
    },

    testimonialBanner() {
        const $slider = this.$("#slider");
        if ($slider.length) {
            $slider.owlCarousel({
                items: 3,
                loop: true,
                margin: 50,
                autoplay: false,
                autoplayTimeout: 3000,
                autoplayHoverPause: true,
                nav: true,
                dots: true,
                responsive: {
                    0: { items: 1 },
                    600: { items: 2 },
                    1000: { items: 3, dots: true },
                },
            });
        }
    },
});

export default publicWidget.registry.Testimonial;
