/** @odoo-module **/
/**
 * "Petzen Categories" snippet (s_petzen_categories): loads the "Shop by Category"
 * tiles from the backend (/petzen/snippet/categories → website._petzen_category_cards:
 * one tile per "Pets Category"). Used on the home and shop pages and from the blocks panel.
 */
import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";
import { renderToElement } from "@web/core/utils/render";

publicWidget.registry.PetzenCategoriesSnippet = publicWidget.Widget.extend({
    selector: ".s_petzen_categories",
    // also shown in the website editor (the generated content is removed before saving)
    disabledInEditableMode: false,

    async willStart() {
        await this._super(...arguments);
        try {
            this.cards = await rpc("/petzen/snippet/categories", {
                limit: parseInt(this.el.dataset.limit, 10) || 5,
            });
        } catch {
            this.cards = [];
        }
    },

    start() {
        this._renderCategories();
        return this._super(...arguments);
    },

    destroy() {
        this._super(...arguments);
        this._clearCategories();
    },

    _renderCategories() {
        const bentoEl = this.el.querySelector(".categories-bento");
        const cards = this.cards || [];
        this._clearCategories();
        bentoEl?.replaceChildren(...cards.map((card, index) =>
            renderToElement("theme_petzen.CategoriesSnippetCard", { card, large: index === 0 })
        ));
        bentoEl?.classList.toggle("d-none", !cards.length);
        this.el.querySelector(".pz-categories-empty")?.classList.toggle("d-none", !!cards.length);
    },

    /** Generated content must not be saved in the page by the website editor. */
    _clearCategories() {
        const bentoEl = this.el.querySelector(".categories-bento");
        bentoEl?.replaceChildren();
        bentoEl?.classList.remove("d-none");
        this.el.querySelector(".pz-categories-empty")?.classList.add("d-none");
    },
});
