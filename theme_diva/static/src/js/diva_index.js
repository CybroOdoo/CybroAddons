import publicWidget from "@web/legacy/js/public/public_widget";
import animations from "@website/js/content/snippets.animation";

publicWidget.registry.shopCollection = animations.Animation.extend({
    selector: '.shop_collection_class',
    async start() {
        $.get("/shop_collection_data", (data) => {
            this.$target.empty().append(data);

            $("#shop_collection_slider").owlCarousel({
                loop: true,
                smartSpeed: 450,
                autoplay: true,
                autoplayTimeout: 1000,
                autoplayHoverPause: true,
                dots: true,
                nav: true,
                navText: [
                    '<i class="bi bi-arrow-left-circle-fill"></i>',
                    '<i class="bi bi-arrow-right-circle-fill"></i>'
                ],
                animateOut: 'fadeOut',
                responsive: {
                    0: {
                        items: 1
                    },
                    768: {
                        items: 3
                    },
                }
            });

            // Animate On Scroll
            AOS.init({
                easing: 'ease-in-quad',

            });
        });
    }
});
