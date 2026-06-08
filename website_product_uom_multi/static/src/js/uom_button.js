/** @odoo-module **/

import { patch } from '@web/core/utils/patch';
import { WebsiteSale } from '@website_sale/interactions/website_sale';


/**
 * Patch WebsiteSale interaction to include UOM in price calculations and cart updates.
 */
patch(WebsiteSale.prototype, {
    /**
     * @override
     * Handle UOM dropdown changes.
     */
    setup() {
        super.setup();
        if (this.el) {
            // Use event delegation on the main container to capture UOM dropdown changes.
            this.el.addEventListener('change', (ev) => {
                const target = ev.target;
                if (target && target.id === 'o_uom_dropdown') {
                    // We call _getCombinationInfo instead of onChangeVariant
                    // to avoid "currentTarget.closest is not a function" errors
                    // as Odoo's onChangeVariant expects currentTarget to be the product container.
                    this._getCombinationInfo(ev);
                }
            });
        }
    },

    /**
     * @override
     * Ensure the selected UOM is included in the rootProduct object for cart additions.
     */
    _updateRootProduct(form) {
        super._updateRootProduct(form);
        const uomId = this._getUoMId(form);
        if (uomId) {
            this.rootProduct.uomId = uomId;
        }
    },

    /**
     * @override
     * Provide the UOM ID for variant combinations and price recalculations.
     */
    _getUoMId(element) {
        // Find the dropdown in the specific product/variant context
        const productEl = element.closest('.js_product') || element;
        const uomSelect = productEl.querySelector('select#o_uom_dropdown');
        if (uomSelect) {
            const val = parseInt(uomSelect.value);
            if (val) return val;
        }
        return super._getUoMId(element);
    }
});
