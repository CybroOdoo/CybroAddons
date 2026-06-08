/** @odoo-module **/

import { WebsiteSale } from "@website_sale/interactions/website_sale";
import { patch } from "@web/core/utils/patch";

patch(WebsiteSale.prototype, {
    /**
     * @override
     * Hides the variant combination and shows an out-of-stock message
     * when the selected product variant has website_hide_variants = true.
     */
    _onChangeCombination(ev, parent, combination) {
        const isHidden = !!combination.website_hide_variants;

        if (isHidden) {
            // Mark the combination as not purchasable before super runs
            combination.is_combination_possible = false;
        }

        // Call the original method (via VariantMixin copied to prototype)
        super._onChangeCombination(ev, parent, combination);

        // Find the out-of-stock message div (injected via XML template)
        const msgEl =
            parent.querySelector('#website_hide_variants_msg') ||
            parent.closest('.oe_website_sale')?.querySelector('#website_hide_variants_msg') ||
            document.querySelector('#website_hide_variants_msg');

        if (msgEl) {
            if (isHidden) {
                msgEl.classList.remove('d-none');
            } else {
                msgEl.classList.add('d-none');
            }
        }
    }
});