
import $ from "@theme_eco_food/js/jquery";
import { rpc } from "@web/core/network/rpc";
import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { renderToElement } from "@web/core/utils/render";


export class ecoFoodFeaturedProducts extends Interaction {
    static selector = '.featured_product_carousal';
    async willStart(){
        var data =  await this.waitFor(rpc('/get_featured_products'))
        if(data){
            this.removeChildren(this.el);
            this.insert(renderToElement('theme_eco_food.eco_food_featured_products_carousel', {
                slides: data,
            }));
            this.product_carousel();
        }
    }
    product_carousel () {
        const carousel = $(this.el).find(".favorite-carousel");
        this.registerCleanup(() => carousel.trigger("destroy.owl.carousel"));
        carousel.owlCarousel(
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
    }
}

registry.category("public.interactions").add("theme_eco_food.ecoFoodFeaturedProducts", ecoFoodFeaturedProducts);
