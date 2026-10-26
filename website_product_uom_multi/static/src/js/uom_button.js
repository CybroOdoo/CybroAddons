/** @odoo-module **/

import { patch } from '@web/core/utils/patch';
import { patchDynamicContent } from '@web/public/utils';
import { ProductPage } from '@website_sale/interactions/product_page';

/**
 * Patch ProductPage interaction to sync UOM dropdown with hidden radio inputs.
 */
patch(ProductPage.prototype, {
    setup() {
        super.setup();
        patchDynamicContent(this.dynamicContent, {
            '#o_uom_dropdown': {
                't-on-change': this.onChangeUomDropdown.bind(this),
            },
        });
    },

    onChangeUomDropdown(ev) {
        const select = ev.currentTarget;
        const parent = select.closest('.js_product') || this.el;
        const uomId = select.value;
        const radio = parent.querySelector(`input.js_uom_radio[value="${uomId}"]`);
        if (radio) {
            radio.checked = true;
        }
        this._triggerVariantChange(parent);
    },
});
