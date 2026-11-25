/**
 * "Petzen Categories" snippet (s_petzen_categories): loads the "Shop by Category"
 * tiles from the backend (/petzen/snippet/categories → website._petzen_category_cards,
 * the same data as the shop page block theme_petzen.pz_category_bento).
 *
 * Odoo 19 interaction: the tiles are inserted with `renderAt`, so they are removed
 * when the interaction stops (the website editor stops it before saving: the
 * generated tiles are never saved in the page, the snippet stays a normal block
 * that can be moved / duplicated / removed).
 */
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { Interaction } from "@web/public/interaction";

export class PetzenCategoriesSnippet extends Interaction {
    static selector = ".s_petzen_categories";

    async willStart() {
        try {
            this.cards = await this.waitFor(rpc("/petzen/snippet/categories", {
                limit: parseInt(this.el.dataset.limit, 10) || 5,
            }));
        } catch {
            this.cards = [];
        }
    }

    start() {
        const bentoEl = this.el.querySelector(".categories-bento");
        const emptyEl = this.el.querySelector(".pz-categories-empty");
        const cards = this.cards || [];
        // content saved by an older version of the snippet
        bentoEl?.replaceChildren();
        if (bentoEl) {
            cards.forEach((card, index) => {
                this.renderAt("theme_petzen.CategoriesSnippetCard", { card, large: index === 0 }, bentoEl);
            });
        }
        bentoEl?.classList.toggle("d-none", !cards.length);
        emptyEl?.classList.toggle("d-none", !!cards.length);
        this.registerCleanup(() => {
            bentoEl?.classList.remove("d-none");
            emptyEl?.classList.add("d-none");
        });
    }
}

registry.category("public.interactions").add("theme_petzen.categories_snippet", PetzenCategoriesSnippet);

// also shown in the website editor
registry.category("public.interactions.edit").add("theme_petzen.categories_snippet", {
    Interaction: PetzenCategoriesSnippet,
});
