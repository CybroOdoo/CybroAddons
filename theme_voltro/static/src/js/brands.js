import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";

export class BrandCarousel extends Interaction {
    static selector = ".brands";

    start() {
        const carouselEl = this.el.querySelector(".brands_carousel");
        if (!carouselEl) {
            return;
        }
        // Looping a carousel shorter than one page would show duplicated slides
        const perPage = 5;
        const canLoop = carouselEl.querySelectorAll(".splide__slide").length > perPage;
        const carousel = new Splide(carouselEl, {
            type: canLoop ? "loop" : "slide",
            rewind: true,
            perPage,
            gap: 20,
            autoplay: true,
            interval: 3000,
            pauseOnHover: true,
            arrows: false,
            pagination: false,
            breakpoints: {
                600: { perPage: 2 },
                400: { perPage: 1 },
            },
        }).mount();
        this.registerCleanup(() => carousel.destroy());
    }
}

registry.category("public.interactions").add("theme_voltro.brands", BrandCarousel);
