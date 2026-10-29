/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { ProductPage } from "@website_sale/interactions/product_page";


/**
 * Extends the Odoo Website Sale ProductPage to handle product
 * quantity increment and decrement based on the configured
 * minimum, maximum, and step values.
 */
patch(ProductPage.prototype, {
    incOrDecQuantity(ev) {
        const input = ev.currentTarget.closest('.input-group').querySelector('input');
        const min = parseFloat(input.dataset.min || 0);
        const max = parseFloat(input.dataset.max || Infinity);
        const previousQty = parseFloat(input.value || 0);
        const step = parseFloat(input.getAttribute('step') || 0.1);
        const quantity = (
            ev.currentTarget.name === 'minus_button' ? -step : step
        ) + previousQty;
        const newQt = quantity > min ? (quantity < max ? quantity : max) : min;
        const newQty = Math.round(newQt * 100) / 100;

        if (newQty !== previousQty) {
            input.value = newQty;
            // Trigger `onChangeAddQuantity`.
            input.dispatchEvent(new Event('change', { bubbles: true }));
        }
        this._updateMinusButtonTitle(input);
    }
});
