/**
 * "Petzen Products" snippet (s_petzen_products): loads the tabs and product cards
 * from the backend (/petzen/snippet/products → website._petzen_snippet_products:
 * published products in internal categories marked "Show in Petzen Snippets"),
 * then runs the tabs / carousel of the theme (PetzenProducts, petzen.js).
 *
 * The cards are inserted with `renderAt`, which starts the Odoo interactions of
 * the inserted elements only (add to cart: website_sale.add_to_cart_snippet,
 * wishlist: website_sale_wishlist) and removes them when the interaction is
 * stopped, so the generated content is never saved by the website editor.
 * Starting the interactions on the snippet itself (this.el) must be avoided: in
 * Odoo 19 it restarts the snippet itself, i.e. infinite recursion.
 */
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { PetzenProducts } from "@theme_petzen/js/petzen";

export class PetzenProductsSnippet extends PetzenProducts {
    static selector = ".s_petzen_products";

    async willStart() {
        try {
            this.data = await this.waitFor(rpc("/petzen/snippet/products", {
                limit: parseInt(this.el.dataset.limit, 10) || 12,
            }));
        } catch {
            this.data = { tabs: [], products: [] };
        }
    }

    start() {
        this.renderProducts();
        super.start();
    }

    renderProducts() {
        const tabsEl = this.el.querySelector(".products-tabs");
        const rowEl = this.el.querySelector(".products-row");
        const emptyEl = this.el.querySelector(".pz-products-empty");
        const carouselEl = this.el.querySelector(".carousel-wrap");
        const { tabs = [], products = [], wishlist = false } = this.data || {};
        // content saved by an older version of the snippet
        tabsEl?.replaceChildren();
        rowEl?.replaceChildren();

        if (tabsEl && tabs.length) {
            this.renderAt("theme_petzen.ProductsSnippetTabs", { tabs }, tabsEl);
        }
        if (rowEl) {
            for (const product of products) {
                this.renderAt("theme_petzen.ProductsSnippetCard", { product, wishlist }, rowEl);
            }
        }
        tabsEl?.classList.toggle("d-none", !tabs.length);
        carouselEl?.classList.toggle("d-none", !products.length);
        emptyEl?.classList.toggle("d-none", !!products.length);
        this.registerCleanup(() => {
            tabsEl?.classList.remove("d-none");
            carouselEl?.classList.remove("d-none");
            emptyEl?.classList.add("d-none");
        });
    }
}

registry.category("public.interactions").add("theme_petzen.products_snippet", PetzenProductsSnippet);

// also shown in the website editor (without autoplay)
registry.category("public.interactions.edit").add("theme_petzen.products_snippet", {
    Interaction: PetzenProductsSnippet,
    mixin: (I) => class extends I {
        setup() {
            super.setup();
            this.isEditMode = true;
        }
    },
});
