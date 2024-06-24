/** @odoo-module **/

import { jsonrpc } from "@web/core/network/rpc_service";
import publicWidget from "@web/legacy/js/public/public_widget";
import animations from "@website/js/content/snippets.animation";
import { renderToElement } from "@web/core/utils/render";

publicWidget.registry.ecoFoodNewArrival = animations.Animation.extend({
    selector : '.new_arrival_products',
    async start() {
        const data = await jsonrpc('/get_new_arrivals')
        if(data){
            this.$target.empty().append(renderToElement('theme_eco_food.eco_food_new_arrivals_carousel', {
                new_arrival: data,
          }));
          this.product_carousel();
        }
    },
    product_carousel(autoplay=false, items=5, slider_timing=5000) {
        $(".new_arrival_carousel").owlCarousel(
            {
                items: 6,
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
                responsive: {
                    0: {
                        items: 1,
                    },
                    576: {
                        items: 2,
                    },
                    768: {
                        items: 3,
                    },
                    992: {
                        items: 6,
                    }
                },
            }
        );
    },
});