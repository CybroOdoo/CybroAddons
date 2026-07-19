/** @odoo-module **/

import { VariantMixin } from "@website_sale/js/sale_product_configurator";
import { patch } from "@web/core/utils/patch";
import { WebsiteSale } from "@website_sale/js/website_sale";

/**
 * Patch WebsiteSale to intercept combination info responses
 * and show an "This product is unavailable" notice when
 * is_website_hide_variants is True for the selected variant.
 */
patch(WebsiteSale.prototype, "website_hide_variants.WebsiteSale", {

    /**
     * Called by the framework after every combination update
     * (attribute click, page load, etc.).
     */
    _onChangeCombination(ev, $parent, combination) {
        this._super(...arguments);
        this._toggleHideVariantNotice($parent, combination);
    },

    /**
     * Show or hide the unavailability banner based on the
     * `is_website_hide_variants` flag returned by _get_combination_info.
     */
    _toggleHideVariantNotice($parent, combination) {
        const $addToCartWrapper = $parent.find(".o_add_cart_btn_wrapper, #add_to_cart_wrap, #product_add_to_cart");
        const $existingNotice = $parent.find(".o_variant_unavailable_notice");

        if (combination.is_website_hide_variants) {
            // Hide the add-to-cart button area
            $addToCartWrapper.addClass("d-none");

            // Insert the notice if not already there
            if (!$existingNotice.length) {
                const notice = `
                    <div class="o_variant_unavailable_notice alert alert-warning d-flex align-items-center gap-2 mt-2" role="alert">
                        <i class="fa fa-exclamation-triangle fa-lg text-warning"></i>
                        <span>This product variant is <strong>currently unavailable</strong> in our online shop.</span>
                    </div>`;
                $addToCartWrapper.after(notice);
            }
        } else {
            // Restore button, remove notice
            $addToCartWrapper.removeClass("d-none");
            $existingNotice.remove();
        }
    },
});
