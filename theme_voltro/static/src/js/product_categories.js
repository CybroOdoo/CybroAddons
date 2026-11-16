import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

export class ProductCategories extends Interaction {
    static selector = ".featured_categories";

    async willStart() {
        this.content = await rpc("/theme_voltro/product_categories");
    }

    start() {
        if (!this.content) {
            return;
        }
        const placeholder = this.el.innerHTML;
        this.el.innerHTML = this.content;
        this.registerCleanup(() => {
            this.el.innerHTML = placeholder;
        });
        const carouselEl = this.el.querySelector(".featured_product_carousel");
        if (carouselEl) {
            // Looping a carousel shorter than one page would show duplicated slides
            const perPage = 6;
            const canLoop = carouselEl.querySelectorAll(".splide__slide").length > perPage;
            const carousel = new Splide(carouselEl, {
                type: canLoop ? "loop" : "slide",
                rewind: true,
                perPage,
                gap: 20,
                autoplay: true,
                interval: 5000,
                pauseOnHover: true,
                arrows: false,
                pagination: true,
                breakpoints: {
                    900: { perPage: 4 },
                    600: { perPage: 3 },
                    400: { perPage: 2 },
                },
            }).mount();
            this.registerCleanup(() => carousel.destroy());
        }
    }
}

registry.category("public.interactions").add("theme_voltro.product_categories", ProductCategories);
