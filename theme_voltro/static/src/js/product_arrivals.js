import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

export class ProductArrivals extends Interaction {
    static selector = ".new_arrivals";

    async willStart() {
        this.content = await rpc("/theme_voltro/product_arrivals");
    }

    start() {
        if (!this.content) {
            return;
        }
        const placeholder = this.el.innerHTML;
        this.el.innerHTML = this.content;
        // Only handle the interactions of the inserted content: acting on
        // this.el would also target this interaction itself.
        const contentEls = [...this.el.children];
        const interactions = this.services["public.interactions"];
        this.registerCleanup(() => {
            contentEls.forEach((el) => interactions.stopInteractions(el));
            this.el.innerHTML = placeholder;
        });
        contentEls.forEach((el) => interactions.startInteractions(el));
        const carouselEl = this.el.querySelector(".new_arrivals_carousel");
        if (carouselEl) {
            // Looping a carousel shorter than one page would show duplicated slides
            const perPage = 4;
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
                    1000: { perPage: 3 },
                    800: { perPage: 2 },
                    600: { perPage: 1 },
                },
            }).mount();
            this.registerCleanup(() => carousel.destroy());
        }
    }
}

registry.category("public.interactions").add("theme_voltro.product_arrivals", ProductArrivals);
