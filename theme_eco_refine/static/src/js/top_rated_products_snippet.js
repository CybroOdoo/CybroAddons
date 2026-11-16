import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { renderToElement } from "@web/core/utils/render";

export function _chunk(array, size) {
    const result = [];
    for (let i = 0; i < array.length; i += size) {
        result.push(array.slice(i, i + size));
    }
    return result;
}

export class TopRatedProducts extends Interaction {
    static selector = ".top_rated_product_snippet";

    async willStart() {
        const [products, categories, website_id] = await this.waitFor(
            rpc("/top_rated_products", {})
        );
        this.products = products;
        this.categories = categories;
        this.websiteId = website_id;
    }

    start() {
        const container = this.el.querySelector("#top_rated_carousel");
        if (!container) {
            return;
        }
        container.replaceChildren(
            renderToElement("theme_eco_refine.top_rated_products", {
                products: this.products,
                categories: this.categories,
                current_website_id: this.websiteId,
                chunkData: _chunk(this.products, 4),
            })
        );
        window.$(this.el).find(".owl-carousel").owlCarousel({
            loop: true,
            margin: 10,
            autoplay: true,
            nav: true,
            responsiveClass: true,
            responsive: {
                0: { items: 1, nav: true },
                600: { items: 3, nav: true },
                1000: { items: 4, nav: true },
            },
        });
    }

    destroy() {
        window.$(this.el).find(".owl-carousel").trigger("destroy.owl.carousel");
    }
}

registry
    .category("public.interactions")
    .add("theme_eco_refine.top_rated_products", TopRatedProducts);