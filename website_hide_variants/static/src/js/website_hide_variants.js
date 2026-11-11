/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import { ProductPage } from "@website_sale/interactions/product_page";

/**
 * Patch the product page interaction to show a "This product variant is
 * currently unavailable" notice and hide the add to cart button when
 * is_website_hide_variants is True for the selected variant.
 */
patch(ProductPage.prototype, {
    /**
     * Called after every combination update (attribute click, page load, etc.).
     */
    async _onChangeCombination(ev, parent, combination) {
        await super._onChangeCombination(...arguments);
        this._toggleHideVariantNotice(parent, combination);
    },

    /**
     * Show or hide the unavailability banner based on the
     * `is_website_hide_variants` flag returned by _get_combination_info.
     * When the variant is not hidden, the add to cart button is left as
     * website_sale set it (it may be hidden for other reasons).
     *
     * @param {Element} parent
     * @param {Object} combination
     */
    _toggleHideVariantNotice(parent, combination) {
        const addToCartWrap = parent.querySelector("#add_to_cart_wrap");
        const existingNotice = parent.querySelector(".o_variant_unavailable_notice");

        if (!combination.is_website_hide_variants) {
            existingNotice?.remove();
            return;
        }
        if (addToCartWrap) {
            addToCartWrap.classList.remove("d-inline-flex");
            addToCartWrap.classList.add("d-none");
        }
        if (existingNotice) {
            return;
        }
        const notice = document.createElement("div");
        notice.className =
            "o_variant_unavailable_notice alert alert-warning d-flex align-items-center gap-2 mt-2";
        notice.setAttribute("role", "alert");
        const icon = document.createElement("i");
        icon.className = "fa fa-exclamation-triangle fa-lg text-warning";
        const message = document.createElement("span");
        message.textContent = _t(
            "This product variant is currently unavailable in our online shop."
        );
        notice.append(icon, message);
        if (addToCartWrap) {
            addToCartWrap.after(notice);
        } else {
            parent.append(notice);
        }
    },
});
