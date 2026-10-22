import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { renderToElement } from "@web/core/utils/render";

export class TopSellingProducts extends Interaction {
    static selector = ".products_category_wise_snippet";

    async willStart() {
        const data = await rpc("/top_products/categories", {});
        this.products = data[0] || [];
        this.categories = data[1] || [];
        this.websiteId = data[2] || false;
    }

    start() {
        const products = this.products;
        const categories = this.categories;
        const currentWebsiteId = this.websiteId;
        const productsList = [];

        categories.forEach((category) => {
            const categoryProducts = products.filter(
                (product) =>
                    Array.isArray(product.public_categ_ids) &&
                    product.public_categ_ids.includes(category.id)
            );

            if (!categoryProducts.length) {
                return;
            }

            const chunks = [];
            for (let i = 0; i < categoryProducts.length; i += 4) {
                chunks.push(categoryProducts.slice(i, i + 4));
            }
            if (chunks.length > 1) {
                chunks[0].is_active = true;
                chunks.push("chunk");
            }
            productsList.push({
                category,
                products: chunks,
            });
        });

        const content = renderToElement(
            "top_selling_products_in_category.products_category_wise",
            {
                products,
                categories,
                current_website_id: currentWebsiteId,
                products_list: productsList,
            }
        );

        const targetEl = this.el.querySelector("#top_products_carousel");
        if (targetEl) {
            targetEl.innerHTML = "";
            targetEl.appendChild(content);
        }

        const emptyDivs = this.el.querySelectorAll(".top_selling");
        emptyDivs.forEach((div) => {
            if (!div.firstElementChild) {
                div.remove();
            }
        });

        const carouselItems = this.el.querySelectorAll(".top");
        carouselItems.forEach((item) => {
            if (!item.firstElementChild) {
                item.remove();
            }
        });
    }
}

registry
    .category("public.interactions")
    .add("top_selling_products_in_category.top_selling_products", TopSellingProducts);
