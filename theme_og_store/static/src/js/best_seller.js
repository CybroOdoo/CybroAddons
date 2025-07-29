/** @odoo-module */

import { renderToElement } from "@web/core/utils/render";
import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

publicWidget.registry.BestSeller = publicWidget.Widget.extend({
    selector : '.best_seller_section',
    async willStart() {
        const result = await rpc('/get_best_sellers', {});
        if(result){
            this.$target.empty().html(renderToElement('theme_og_store.best_seller_data', {result: result}))
        }
    },
    start() {
        this._super(...arguments);
        this._initializeCarousel();
    },

    _initializeCarousel() {
        const $slider = this.$('#carousel-1');
        if (!$slider.length) return;

        // Initialize Owl Carousel
        $slider.owlCarousel({
                  loop: true,
                  margin: 10,
                  responsiveClass: true,
                  responsive: {
                    0: {
                      items: 1,
                      nav: true
                    },
                    600: {
                      items: 3,
                      nav: false
                    },
                    1000: {
                      items: 8,
                      nav: true,
                      loop: false,
                      margin: 20
                    }
                  }
        });
    },

});














///** @odoo-module **/
//import publicWidget from "@web/legacy/js/public/public_widget";
//import animations from "@website/js/content/snippets.animation";
//import { rpc } from "@web/core/network/rpc";
//
//publicWidget.registry.shopFunction = animations.Animation.extend({
//    selector: ".best_seller_section",
//
//    start: async function () {
//        // To get data from controller.
//        var self = this;
////        self.recommendCarousel();
//        await rpc('/get_best_sellers', {}).then(function(data) {
//            if (data) {
////                self.$('#best_seller').html(data);
////                self.BestsellerCarousel();
////                self.recommendCarousel();
//
//            }
//        })
//        },
//
//    BestsellerCarousel: function() {
//        const $slider = this.$('#carousel-1');
//        if ($slider.length) {
//            $slider.owlCarousel({
//                  loop: true,
//                  margin: 10,
//                  responsiveClass: true,
//                  responsive: {
//                    0: {
//                      items: 1,
//                      nav: true
//                    },
//                    600: {
//                      items: 3,
//                      nav: false
//                    },
//                    1000: {
//                      items: 5,
//                      nav: true,
//                      loop: false,
//                      margin: 20
//                    }
//                  }
//            })
//        }
//        },
//
//    recommendCarousel: function() {
//        const $slider = this.$('#carousel');
//        $('#carousel').owlCarousel({
//            loop: true,
//            margin: 10,
//            responsiveClass: true,
//            responsive: {
//              0: {
//                items: 1,
//                nav: true
//              },
//              600: {
//                items: 3,
//                nav: false
//              },
//              1000: {
//                items: 5,
//                nav: true,
//                loop: false,
//                margin: 20
//              }
//            }
//          })
//    },
//
//});
//
//export default publicWidget.registry.shopFunction;
