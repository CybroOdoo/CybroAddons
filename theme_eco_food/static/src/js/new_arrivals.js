
import $ from "@theme_eco_food/js/jquery";
import { rpc } from "@web/core/network/rpc";
import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { renderToElement } from "@web/core/utils/render";

export class ecoFoodNewArrival extends Interaction {
    static selector = '.new_arrival_products';
    async willStart() {
        const data = await this.waitFor(rpc('/get_new_arrivals'))
        if(data){
            this.removeChildren(this.el);
            this.insert(renderToElement('theme_eco_food.eco_food_new_arrivals_carousel', {
                new_arrival: data,
          }));
          this.product_carousel();
        }
    }
    product_carousel() {
        const carousel = $(this.el).find(".new_arrival_carousel");
        this.registerCleanup(() => carousel.trigger("destroy.owl.carousel"));
        carousel.owlCarousel(
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
                }
            }
        );
    }
}

registry.category("public.interactions").add("theme_eco_food.ecoFoodNewArrival", ecoFoodNewArrival);
