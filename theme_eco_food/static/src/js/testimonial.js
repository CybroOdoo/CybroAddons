/** @odoo-module **/

import { jsonrpc } from "@web/core/network/rpc_service";
import publicWidget from "@web/legacy/js/public/public_widget";
import animations from "@website/js/content/snippets.animation";
import { renderToElement } from "@web/core/utils/render";

publicWidget.registry.ecoFoodTestimonial = animations.Animation.extend({
    selector : '.testimonial_carousel',
    async start(){
        const data =  await jsonrpc('/get_testimonials')
        if(data){
            this.$target.empty().append(renderToElement('theme_eco_food.eco_food_testimonial_carousel', {
                slides: data
            }));
            this.product_carousel();
        }
    },
    product_carousel () {
        $(".favorite-carousel").owlCarousel(
            {
                items: 1,
                loop: true,
                margin: 40,
                stagePadding: 0,
                smartSpeed: 450,
                autoplay: false,
                autoPlaySpeed: 3000,
                autoPlayTimeout: 1000,
                autoplayHoverPause: true,
                dots: false,
                nav: true,
            }
        );
    },
});