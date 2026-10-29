/** @odoo-module **/
import { markup } from '@odoo/owl';
import { patch } from "@web/core/utils/patch";
import { rpc } from '@web/core/network/rpc';
import { redirect } from '@web/core/utils/urls';
import { browser } from '@web/core/browser/browser';
import wSaleUtils from '@website_sale/js/website_sale_utils';
import { CartLine } from "@website_sale/interactions/cart_line";


/**
 * Extends the website sale cart line functionality to handle
 * product quantity changes from the cart.
 */
patch(CartLine.prototype, {
    async incOrDecQuantity(ev) {
        const input = ev.currentTarget.closest('.css_quantity').querySelector('input.js_quantity');
        const datasetMin = parseFloat(input.dataset.min || 0);
        const minQuantity = datasetMin > 1 ? datasetMin : 0;
        const maxQuantity = parseFloat(input.dataset.max || Infinity);
        const oldQuantity = parseFloat(input.value || 0);
        const step = parseFloat(input.getAttribute('step') || 0.1);
        const newQt = ev.currentTarget.name === 'minus_button'
            ? Math.min(Math.max(oldQuantity - step, minQuantity), maxQuantity)
            : Math.min(oldQuantity + step, maxQuantity);
        const newQuantity = Math.round(newQt * 100) / 100;

        if (oldQuantity !== newQuantity) {
            input.value = newQuantity;
            await this._changeQuantity(input);
        }
    },

    async _changeQuantity(input) {
        let quantity = parseFloat(input.value || 0);
        if (isNaN(quantity)) quantity = 1.0;
        const lineId = parseInt(input.dataset.lineId);
        const data = await this.waitFor(rpc('/shop/cart/update', {
            line_id: lineId,
            product_id: parseInt(input.dataset.productId),
            quantity: quantity,
        }));
        data['website_sale.cart_lines'] = markup(data['website_sale.cart_lines']);
        if (data.tracking_info?.length) {
            wSaleUtils.dispatchTrackingEvent("update_cart_event", {
                currency: data.currency,
                items: data.tracking_info,
            });
        }
        if (!data.cart_quantity) {
            browser.sessionStorage.setItem('website_sale_cart_quantity', 0);
            return redirect('/shop/cart');
        }
        input.value = data.quantity;
        this.el.querySelectorAll(`.js_quantity[data-line-id="${lineId}"]`).forEach(input =>
            input.value = data.quantity
        );
        const cart = this.el.closest('#shop_cart');
        this.services['public.interactions'].stopInteractions(cart);
        wSaleUtils.updateCartNavBar(data);
        wSaleUtils.updateQuickReorderSidebar(data);
        this.services['public.interactions'].startInteractions(cart);
        this.services.cart.showWarning(data.warning);
        this.env.bus.trigger('cart_amount_changed', [data.amount, data.minor_amount]);
    }
});
