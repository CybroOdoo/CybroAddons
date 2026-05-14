/** @odoo-module */
import { PosStore } from "@point_of_sale/app/services/pos_store";
import { patch } from "@web/core/utils/patch";

/**
 * Customizes the behavior of the `productsToDisplay` getter in the ProductScreen.
 * This patch modifies the way products are filtered, sorted, and limited before being displayed
 * based on search input, selected category, and other configurable parameters.
 **/

patch(PosStore.prototype, {
    get productsToDisplay() {
        let list = [];

        if (this.searchProductWord?.trim() !== "") {
            list = this.getProductsBySearchWord(
                this.searchProductWord,
                this.selectedCategory?.id
                    ? this.selectedCategory.associatedProducts
                    : this.models["product.template"].getAll()
            );
        } else if (this.selectedCategory?.id) {
            list = this.selectedCategory.associatedProducts;
        } else {
            list = this.models["product.template"].getAll();
        }

        if (!list || list.length === 0) {
            return [];
        }

        const excludedProductIds = new Set(this.getExcludedProductIds());
        const availableCateg = new Set(
            (this.config.iface_available_categ_ids || []).map((c) => c.id)
        );

        list = list
            .filter(
                (product) =>
                    !excludedProductIds.has(product.id) &&
                    product.canBeDisplayed &&
                    (!availableCateg.size ||
                        product.pos_categ_ids.some((c) => availableCateg.has(c.id)))
            )
            .slice(0, 100);

        let all_items =
            this.searchProductWord?.trim() !== ""
                ? list
                : list.sort((a, b) => a.display_name.localeCompare(b.display_name));

        // Apply product limit from POS configuration
        const limit = this.config.product_limit || 0;
        return limit > 0 ? all_items.slice(0, limit) : all_items;
    },
});
