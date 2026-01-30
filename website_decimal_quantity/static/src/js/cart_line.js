/** @odoo-module **/
import { browser } from '@web/core/browser/browser';
import { rpc } from '@web/core/network/rpc';
import { patch } from '@web/core/utils/patch';
import wSaleUtils from '@website_sale/js/website_sale_utils';
import { CartLine } from '@website_sale/interactions/cart_line';

patch(CartLine.prototype,{
/**
* This module extends the website_sale module to support decimal quantity input when updating products in cart.
* It overrides the incOrDecQuantity and _changeQuantity methods to enable decimal-based quantity adjustments.
* Additionally, it extends the CartLine component to properly handle cart quantity updates when decimal values are entered.
*/
    async incOrDecQuantity(ev, currentTargetEl) {
        const input = currentTargetEl.closest('.css_quantity').querySelector('input.js_quantity');
        const maxQuantity = parseFloat(input.dataset.max || Infinity);
        const oldQuantity = parseFloat(input.value || 0);
        const newQty = currentTargetEl.querySelector('i').classList.contains('oi-minus')
            ? Math.min(Math.max(oldQuantity - 0.1, 0), maxQuantity)
            : Math.min(oldQuantity + 0.1, maxQuantity);
        var newQuantity = newQty.toFixed(1);
        if (oldQuantity !== newQuantity) {
            input.value = newQuantity;
            await this._changeQuantity(input);
        }
    },

    async _changeQuantity(input) {
            let quantity = parseFloat(input.value || 0);
            if (isNaN(quantity) || quantity <= 0) {
                quantity = 0; // or 1.0 if that’s your minimum
            }
            const lineId = parseInt(input.dataset.lineId);
            const data = await this.waitFor(rpc('/shop/cart/update', {
                line_id: lineId,
                product_id: parseInt(input.dataset.productId),
                quantity: quantity,
            }));
            if (!data.cart_quantity) {
                // Ensure the last cart removal is recorded.
                browser.sessionStorage.setItem('website_sale_cart_quantity', 0);
                return window.location = '/shop/cart';
            }
            input.value = data.quantity;
            this.el.querySelectorAll(`.js_quantity[data-line-id="${lineId}"]`).forEach(input =>
                input.value = data.quantity
            );

            const cart = this.el.closest('#shop_cart');
            // `updateCartNavBar` regenerates the cart lines and `updateQuickReorderSidebar`
            // regenerates the quick reorder products, so we need to stop and start interactions
            // to make sure the regenerated cart lines and reorder products are properly handled.
            this.services['public.interactions'].stopInteractions(cart);
            wSaleUtils.updateCartNavBar(data);
            wSaleUtils.updateQuickReorderSidebar(data);
            this.services['public.interactions'].startInteractions(cart);
            wSaleUtils.showWarning(data.warning);
            // Propagate the change to the express checkout forms.
            this.env.bus.trigger('cart_amount_changed', [data.amount, data.minor_amount]);
        }
})
