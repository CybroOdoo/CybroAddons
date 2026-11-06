/** @odoo-module **/
/**
 * "Petzen Products" snippet (s_petzen_products): loads the tabs and product cards
 * from the backend (/petzen/snippet/products → website._petzen_snippet_products:
 * published products of the product categories flagged "Pets Category"),
 * then runs the tabs / carousel of the theme (PetzenProducts, petzen.js).
 * "Add" and wishlist buttons: product_card.js (standard website_sale widgets);
 * quick view: PetzenPage (petzen.js).
 */
import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";
import { renderToElement, renderToFragment } from "@web/core/utils/render";
import { PetzenProducts } from "@theme_petzen/js/petzen";

publicWidget.registry.PetzenProductsSnippet = PetzenProducts.extend({
    selector: ".s_petzen_products",
    // also shown in the website editor (the generated content is removed before saving)
    disabledInEditableMode: false,

    async willStart() {
        await this._super(...arguments);
        try {
            this.data = await rpc("/petzen/snippet/products", {
                limit: parseInt(this.el.dataset.limit, 10) || 12,
            });
        } catch {
            this.data = { tabs: [], products: [] };
        }
    },

    start() {
        this._renderProducts();
        return this._super(...arguments);
    },

    destroy() {
        this._super(...arguments);
        this._clearProducts();
    },

    _renderProducts() {
        const tabsEl = this.el.querySelector(".products-tabs");
        const rowEl = this.el.querySelector(".products-row");
        const emptyEl = this.el.querySelector(".pz-products-empty");
        const { tabs = [], products = [] } = this.data || {};
        this._clearProducts();
        if (tabsEl) {
            tabsEl.replaceChildren(renderToFragment("theme_petzen.ProductsSnippetTabs", { tabs }));
            tabsEl.classList.toggle("d-none", !tabs.length);
        }
        if (rowEl) {
            rowEl.replaceChildren(...products.map((product) =>
                renderToElement("theme_petzen.ProductsSnippetCard", { product })
            ));
        }
        emptyEl?.classList.toggle("d-none", !!products.length);
        this.el.querySelector(".carousel-wrap")?.classList.toggle("d-none", !products.length);
    },

    /** Generated content must not be saved in the page by the website editor. */
    _clearProducts() {
        this.el.querySelector(".products-tabs")?.replaceChildren();
        this.el.querySelector(".products-row")?.replaceChildren();
        this.el.querySelector(".c-dots")?.replaceChildren();
        this.el.querySelector(".products-tabs")?.classList.remove("d-none");
        this.el.querySelector(".carousel-wrap")?.classList.remove("d-none");
        this.el.querySelector(".pz-products-empty")?.classList.add("d-none");
    },
});
