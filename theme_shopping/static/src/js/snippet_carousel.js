/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { loadCSS, loadJS } from "@web/core/assets";

let owlAssetsPromise;

function ensureOwlAssets() {
    if (!owlAssetsPromise) {
        if (typeof window.$ !== "undefined" && $.fn.owlCarousel) {
            owlAssetsPromise = Promise.resolve();
        } else {
            owlAssetsPromise = Promise.all([
                loadCSS("/theme_shopping/static/src/css/owl.carousel.min.css"),
                loadCSS("/theme_shopping/static/src/css/owl.theme.default.min.css"),
                loadJS("/theme_shopping/static/src/js/owl.carousel.min.js"),
            ]);
        }
    }
    return owlAssetsPromise;
}

publicWidget.registry.OfferSnippet = publicWidget.Widget.extend({
    selector: '.offer_snippet',
    disabledInEditableMode: false,

    start: function() {
        var self = this;
        return this._super.apply(this, arguments).then(function() {
            return ensureOwlAssets();
        }).then(function() {
            self._initCarousel();
        });
    },

    _initCarousel() {
        const $carousel = this.$el.find("#offer_product_carousel");
        if ($carousel.length && $carousel.owlCarousel) {
            // Destroy previous carousel instance if any
            if ($carousel.hasClass('owl-loaded')) {
                $carousel.trigger('destroy.owl.carousel');
                $carousel.removeClass('owl-loaded owl-drag owl-grab');
            }

            $carousel.addClass('owl-carousel');
            $carousel.owlCarousel({
                items: 1,
                loop: true,
                nav: false,
                autoplay: true,
                autoplayTimeout: 3000,
                autoplayHoverPause: true,
                dots: true,
                smartSpeed: 500,
            });
        }
    },
});


// /** @odoo-module */
// import Animation from "@website/js/content/snippets.animation";
// import { loadCSS, loadJS } from "@web/core/assets";

// let owlAssetsPromise;

// function ensureOwlAssets() {
//     if (!owlAssetsPromise) {
//         if (typeof window.$ !== "undefined" && $.fn.owlCarousel) {
//             owlAssetsPromise = Promise.resolve();
//         } else {
//             owlAssetsPromise = Promise.all([
//                 loadCSS("/web/static/lib/owlCarousel/css/owl.carousel.min.css"),
//                 loadCSS("/web/static/lib/owlCarousel/css/owl.theme.default.min.css"),
//                 loadJS("/web/static/lib/owlCarousel/owl.carousel.min.js"),
//             ]);
//         }
//     }
//     return owlAssetsPromise;
// }

// Animation.registry.shopping = Animation.Class.extend({
//     selector: '.offer_snippet',

//     async start() {
//         await this._super(...arguments);
//         await ensureOwlAssets();
//         this.offer_snippet_carousel();
//     },

//     offer_snippet_carousel() {
//         const $carousel = this.$("#offer_product_carousel");
//         if ($carousel.length) {
//             // Destroy existing instance if present
//             if ($carousel.hasClass('owl-loaded')) {
//                 $carousel.trigger('destroy.owl.carousel');
//                 $carousel.removeClass('owl-loaded owl-drag owl-grab');
//             }
            
//             // Add owl-carousel class and initialize
//             $carousel.addClass('owl-carousel');
//             $carousel.owlCarousel({
//                 items: 1,
//                 loop: true,
//                 nav: false,
//                 autoplay: true,
//                 autoplayTimeout: 3000,
//                 autoplayHoverPause: true,
//                 dots: true,
//                 smartSpeed: 500,
//             });
//         }
//     },
// });
