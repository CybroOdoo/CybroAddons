/** @odoo-module **/

import { rpc } from "@web/core/network/rpc";
import publicWidget from "@web/legacy/js/public/public_widget";
import animations from "@website/js/content/snippets.animation";
import { renderToElement } from "@web/core/utils/render";

publicWidget.registry.ecoFoodFeaturedProducts = animations.Animation.extend({
    selector : '.featured_product_carousal',
    async start(){
        var data =  await rpc('/get_featured_products')
        if(data){
            this.$target.empty().append(renderToElement('theme_eco_food.eco_food_featured_products_carousel', {
                slides: data,
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