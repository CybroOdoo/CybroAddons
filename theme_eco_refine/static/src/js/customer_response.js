import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";

/**
 * Customer response snippet: testimonial carousel. owlCarousel is a jQuery plugin, so it still needs the global jQuery.
 */
export class CustomerResponse extends Interaction {
    static selector = ".customer_response";

    start() {
        window.$(this.el).find(".owl-carousel2").owlCarousel({
            items: 1,
            loop: true,
            nav: false,
            autoplay: true,
            dots: false,
        });
    }

    destroy() {
        window.$(this.el).find(".owl-carousel2").trigger("destroy.owl.carousel");
    }
}

registry
    .category("public.interactions")
    .add("theme_eco_refine.customer_response", CustomerResponse);
