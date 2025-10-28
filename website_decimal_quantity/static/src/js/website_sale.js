/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import wSaleUtils from "@website_sale/js/website_sale_utils";
import { Component } from "@odoo/owl";

publicWidget.registry.WebsiteSale.include({
 /**
* This module extends the website_sale module to support decimal quantity input for adding products to the cart.
* It overrides the _onClickAddCartJSON function from sale.VariantMixin to add support for decimal quantity input,
* and extends the WebsiteSale widget to handle updating cart quantities when a decimal quantity is entered.
*/
    _onClickAddCartJSON(ev) {
        ev.preventDefault();
        const $link = $(ev.currentTarget);
        const $input = $link.closest('.input-group').find("input");
        const min = parseFloat($input.attr("min")) || 0.01;
        const max = parseFloat($input.attr("max")) || Infinity;
        const step = parseFloat($input.attr("step")) || 0.1;
        const previousQty = parseFloat($input.val()) || 0;

        const isMinus = $link.find(".fa-minus").length > 0;

        let newQty = isMinus ? previousQty - step : previousQty + step;

        if (newQty < min) newQty = min;
        if (newQty > max) newQty = max;

        const precision = step < 1 ? step.toString().split('.')[1]?.length || 1 : 0;
        newQty = parseFloat(newQty.toFixed(precision));
        $input.val(newQty).trigger('change');
        return false;
    },

    /**  Override the function  _changeCartQuantity for changing the cart quantity **/
    _changeCartQuantity($input, value, $dom_optional, line_id, productIDs) {
        $($dom_optional).toArray().forEach((elem) => {
            $(elem).find('.js_quantity').text(value);
            productIDs.push($(elem).find('span[data-product-id]').data('product-id'));
        });

        $input.data('update_change', true);
        this.rpc("/shop/cart/update_json", {
            line_id: line_id,
            product_id: parseInt($input.data('product-id'), 10),
            set_qty: value,
            display: true,
        }).then((data) => {
            $input.data('update_change', false);
            let check_value = parseFloat($input.val());
            if (isNaN(check_value)) check_value = value;

            if (value !== check_value) {
                $input.trigger('change');
                return;
            }
            if (!data.cart_quantity) {
                return (window.location = '/shop/cart');
            }

            $input.val(data.quantity);
            $('.js_quantity[data-line-id=' + line_id + ']').val(data.quantity).text(data.quantity);

            wSaleUtils.updateCartNavBar(data);
            wSaleUtils.showWarning(data.notification_info.warning);

            // Propagating the change to the express checkout forms
            Component.env.bus.trigger('cart_amount_changed', [data.amount, data.minor_amount]);
        });
    },

   /**  Override the function  _onChangeCartQuantity **/
    _onChangeCartQuantity(ev) {
        ev.preventDefault();
        const $input = $(ev.currentTarget);
        if ($input.data('update_change')) return;

        let value = parseFloat($input.val());
        if (isNaN(value)) {
            value = parseFloat($input.attr("min")) || 0.01;
        } else if (value < 0) {
            value = parseFloat($input.attr("min")) || 0.01;
        }
        const $dom = $input.closest('tr');
        const $dom_optional = $dom.nextUntil(':not(.optional_product.info)');
        const line_id = parseInt($input.data('line-id'), 10);
        const productIDs = [parseInt($input.data('product-id'), 10)];

        this._changeCartQuantity($input, value, $dom_optional, line_id, productIDs);
    },

    async _onClickDelete(ev) {
        ev.preventDefault();
        ev.stopPropagation();

        const tr = ev.currentTarget.closest('tr');
        const line_id = parseInt(tr.dataset.lineId);
        const $input = $(tr).find('.js_quantity');

        if (!line_id || !$input.length) {
            return;
        }

        await this._changeCartQuantity($input, 0, [], line_id, []);

        $(tr).fadeOut(300, () => $(tr).remove());
        setTimeout(() => window.location.reload(), 400);
    }

});
