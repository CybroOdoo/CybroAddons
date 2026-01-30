/** @odoo-module **/
import wSaleUtils from '@website_sale/js/website_sale_utils';
import { patch } from '@web/core/utils/patch';
import { WebsiteSale } from '@website_sale/interactions/website_sale';

patch(WebsiteSale.prototype, {
 /**
* This module extends the website_sale module to support decimal quantity input for adding products to the cart.
* It overrides the onChangeQuantity function from sale.VariantMixin to add support for decimal quantity input,
*/
    onChangeQuantity(ev) {
        const input = ev.currentTarget.closest('.input-group').querySelector('input');
        const min = parseFloat(input.dataset.min || 0);
        const max = parseFloat(input.dataset.max || Infinity);
        const previousQty = parseFloat(input.value || 0);
        const quantity = (
        ev.currentTarget.name === 'remove_one' ? -0.1 : 0.1
        ) + previousQty;
        const newQt = quantity > min ? (quantity < max ? quantity : max) : min;

        if (newQt !== previousQty) {
            var newQty = newQt.toFixed(1);
            input.value = newQty;
            // Trigger `onChangeAddQuantity`.
            input.dispatchEvent(new Event('change', { bubbles: true }));
        }

        newQty = newQt.toFixed(1);
    },
})
