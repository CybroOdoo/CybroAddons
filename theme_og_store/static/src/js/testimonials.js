/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";
import animations from "@website/js/content/snippets.animation";
import { renderToElement } from "@web/core/utils/render";


publicWidget.registry.Testimonial = animations.Animation.extend({
    selector: ".testimonial_section",

    async willStart() {
         this.$target.empty().html(renderToElement('theme_og_store.testimonial_data'))

    },
   start() {
        this._super(...arguments);
        this.testimonialBanner();
    },


    testimonialBanner: function() {
            const $slider = this.$('#slider');
            if ($slider.length) {
                $slider.owlCarousel({
                  items: 3,
                  loop: true,           // Enable continuous loop mode
                  margin: 50,           // Space between items
                  autoplay: false,       // Enable auto scroll
                  autoplayTimeout: 3000, // Time interval for auto scroll (3 seconds)
                  autoplayHoverPause: true, // Pause on hover

                  nav: true,     // Enable navigation (arrows)
                  dots: true,    // Enable pagination dots
                  responsive: {
                    0: {
                      items: 1              // Show 1 item for screen widths 0px and up
                    },
                    600: {
                      items: 2               // Show 2 items for screen widths 600px and up
                    },
                    1000: {
                      items: 3,               // Show 3 items for screen widths 1000px and up
                      dots: true,
                    }
                  }
                });
            }
    }
});

export default publicWidget.registry.Testimonial;
