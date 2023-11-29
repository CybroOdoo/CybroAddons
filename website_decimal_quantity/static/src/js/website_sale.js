odoo.define('website_decimal_qty.website_sale', function (require) {
'use strict';

    var publicWidget = require('web.public.widget');
    var wSaleUtils = require('website_sale.utils');
    const dom = require('web.dom');
    require('website_sale.website_sale');
    /**
    * This module extends the website_sale module to support decimal quantity input for adding products to the cart.
    * It overrides the onClickAddCartJSON function from sale.VariantMixin to add support for decimal quantity input,
    * and extends the WebsiteSale widget to handle updating cart quantities when a decimal quantity is entered.
    */
    publicWidget.registry.WebsiteSale.include({
        /**Override the function _changeCartQuantity to set decimal qty **/
        _changeCartQuantity: function ($input, value, $dom_optional, line_id, productIDs) {
            _.each($dom_optional, function (elem) {
                $(elem).find('.js_quantity').text(value);
                productIDs.push($(elem).find('span[data-product-id]').data('product-id'));
            });
            $input.data('update_change', true);
            this._rpc({
                route: "/shop/cart/update_json",
                params: {
                    line_id: line_id,
                    product_id: parseInt($input.data('product-id'), 10),
                    set_qty: value
                },
            }).then(function (data) {
                $input.data('update_change', false);
                var check_value = parseFloat($input.val());
                if (isNaN(check_value)) {
                    check_value = 1;
                }
                if (value !== check_value) {
                    $input.trigger('change');
                    return;
                }
                if (!data.cart_quantity) {
                    return window.location = '/shop/cart';
                }
                wSaleUtils.updateCartNavBar(data);
                $input.val(data.quantity);
                $('.js_quantity[data-line-id='+line_id+']').val(data.quantity).text(data.quantity);
                if (data.warning) {
                    var cart_alert = $('.oe_cart').parent().find('#data_warning');
                    if (cart_alert.length === 0) {
                        $('.oe_cart').prepend('<div class="alert alert-danger alert-dismissable" role="alert" id="data_warning">'+
                                '<button type="button" class="close" data-dismiss="alert" aria-hidden="true">&times;</button> ' + data.warning + '</div>');
                    }
                    else {
                        cart_alert.html('<button type="button" class="close" data-dismiss="alert" aria-hidden="true">&times;</button> ' + data.warning);
                    }
                    $input.val(data.quantity);
                }
            });
        },
        /**Override the function _onChangeCartQuantity to set decimal qty **/
        _onChangeCartQuantity: function (ev) {
            var $input = $(ev.currentTarget);
            if ($input.data('update_change')) {
                return;
            }
            var value = parseFloat($input.val() || 0, 10);
            if (isNaN(value)) {
                value = 1;
            }
            var $dom = $input.closest('tr');
            var $dom_optional = $dom.nextUntil(':not(.optional_product.info)');
            var line_id = parseInt($input.data('line-id'), 10);
            var productIDs = [parseInt($input.data('product-id'), 10)];
            this._changeCartQuantity($input, value, $dom_optional, line_id, productIDs);
        },
    });
})
