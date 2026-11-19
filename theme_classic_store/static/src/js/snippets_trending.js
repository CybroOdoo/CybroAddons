import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { uniqueId } from "@web/core/utils/functions";

/**
 * Number of products per slide, same breakpoints as the former Owl Carousel
 * configuration: < 600px => 1, >= 600px => 2, >= 1000px => 3.
 * Ordered from the widest to the narrowest breakpoint.
 */
const BREAKPOINTS = [
    { minWidth: 1000, items: 3 },
    { minWidth: 600, items: 2 },
];

/**
 * "Trending products" snippet.
 *
 * Odoo 20: jQuery (and therefore the Owl Carousel jQuery plugin) is gone, and
 * so is `PublicWidget`. The slider is now a standard Bootstrap carousel: the
 * markup is rendered with one slide per group of products and Odoo's own
 * `website.carousel_slider` interaction (selector `.carousel`) starts it
 * because `renderAt` activates the interactions of the inserted nodes.
 */
export class ClassicStoreTrending extends Interaction {
    static selector = ".trending_snippet_section";

    setup() {
        this.products = [];
        this.itemsPerSlide = 0;
        this.renderedEls = [];
        this.carouselId = uniqueId("classic_store_trending_");
    }

    async willStart() {
        const result = await this.waitFor(rpc("/classic_product_trending", {}));
        this.products = result?.trending_products || [];
    }

    start() {
        if (!this.products.length) {
            return;
        }
        // Re-render (different number of products per slide) when a
        // breakpoint is crossed.
        for (const { minWidth } of BREAKPOINTS) {
            const mediaQuery = window.matchMedia(`(min-width: ${minWidth}px)`);
            this.addListener(mediaQuery, "change", () => this.render());
        }
        this.render();
    }

    getItemsPerSlide() {
        const breakpoint = BREAKPOINTS.find(
            ({ minWidth }) => window.matchMedia(`(min-width: ${minWidth}px)`).matches
        );
        return breakpoint ? breakpoint.items : 1;
    }

    render() {
        const itemsPerSlide = this.getItemsPerSlide();
        if (itemsPerSlide === this.itemsPerSlide) {
            return;
        }
        this.itemsPerSlide = itemsPerSlide;
        this.clear();

        const slides = [];
        for (let i = 0; i < this.products.length; i += itemsPerSlide) {
            slides.push(this.products.slice(i, i + itemsPerSlide));
        }
        this.renderedEls = this.renderAt(
            "theme_classic_store.s_classic_store_trending_snippet",
            {
                carouselId: this.carouselId,
                slides,
                columnClass: `col-${12 / itemsPerSlide}`,
            },
            this.el
        );
    }

    /**
     * Stops the interactions started on the previous carousel (Bootstrap
     * instance, listeners, ...) before removing it from the DOM.
     */
    clear() {
        for (const el of this.renderedEls) {
            this.services["public.interactions"].stopInteractions(el);
            el.remove();
        }
        this.renderedEls = [];
    }
}

registry
    .category("public.interactions")
    .add("theme_classic_store.trending", ClassicStoreTrending);