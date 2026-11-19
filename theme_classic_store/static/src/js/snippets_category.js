import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

/**
 * "Categories" snippet: fetches the main categories and renders them inside
 * the (empty) `.main_snippet_section` placeholder of the snippet.
 *
 * Odoo 20: replaces the legacy `PublicWidget` (removed together with jQuery)
 * by an `Interaction`.
 */
export class ClassicStoreCategories extends Interaction {
    static selector = ".main_snippet_section";

    setup() {
        this.result = null;
    }

    async willStart() {
        // `waitFor` ignores the result if the interaction was destroyed
        // meanwhile (e.g. the user switched the page to edit mode).
        this.result = await this.waitFor(rpc("/classic_product_category", {}));
    }

    start() {
        if (!this.result) {
            return;
        }
        // Same behaviour as the former `this.$target.empty().html(...)`, but
        // the original content is put back when the interaction is destroyed.
        this.removeChildren(this.el);
        this.renderAt(
            "theme_classic_store.s_classic_store_categories_snippet",
            { result: this.result },
            this.el
        );
    }
}

registry
    .category("public.interactions")
    .add("theme_classic_store.categories", ClassicStoreCategories);