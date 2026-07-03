/** @odoo-module **/

import { PosStore } from "@point_of_sale/app/store/pos_store";
import { patch } from "@web/core/utils/patch";
import { ProductsPopup } from "@pos_multi_variant/js/ProductPopup";

/**
 * Patch PosStore to:
 * 1. Load variants_tree and product_attribute_value into pos state.
 * 2. Intercept addProductToCurrentOrder for multi-variant products.
 */
patch(PosStore.prototype, {
    async _processData(loadedData) {
        await super._processData(...arguments);
        this.variants_tree = loadedData["variants.tree"] || [];
        this.product_attribute_value = loadedData["product.attribute.value"] || [];
    },

    async addProductToCurrentOrder(product, options = {}) {
        if (Number.isInteger(product)) {
            product = this.db.get_product_by_id(product);
        }
        if (!product) return;

        if (product.is_pos_variants) {
            // Get the product template id - it's a [id, name] tuple in POS
            const tmplId = Array.isArray(product.product_tmpl_id)
                ? product.product_tmpl_id[0]
                : product.product_tmpl_id;

            // Filter variant trees matching this product template
            const variants = this.variants_tree.filter((v) => {
                const vid = Array.isArray(v.variants_id) ? v.variants_id[0] : v.variants_id;
                return vid === tmplId;
            });

            // Get the attribute values used by those variant trees
            const allValueIds = new Set();
            variants.forEach((v) => v.value_ids.forEach((id) => allValueIds.add(id)));
            const variantDetails = this.product_attribute_value.filter((v) =>
                allValueIds.has(v.id)
            );

            const { confirmed, payload } = await this.popup.add(ProductsPopup, {
                title: product.display_name,
                products: variants,
                product_tmpl_id: product.id,
                variant_details: variantDetails,
            });

            if (!confirmed) return;

            // Add the product normally (this resets the number buffer, etc.)
            this.get_order() || this.add_new_order();
            const baseOptions = {
                ...(await product.getAddProductOptions()),
                ...options,
            };
            if (!Object.keys(baseOptions).length) return;
            await this.addProductFromUi(product, baseOptions);

            // Attach selected variants to the newly added orderline
            const selectedLine = this.get_order()?.get_selected_orderline();
            if (selectedLine && payload && payload.length > 0) {
                selectedLine.product_variants = payload;
                // Accumulate extra prices
                const extraPrice = payload.reduce(
                    (sum, v) => sum + parseFloat(v.extra_price || 0),
                    0
                );
                if (extraPrice) {
                    selectedLine.set_unit_price(selectedLine.get_unit_price() + extraPrice);
                    selectedLine.price_type = "manual";
                }
            }
            this.numberBuffer.reset();
        } else {
            await super.addProductToCurrentOrder(product, options);
        }
    },
});
