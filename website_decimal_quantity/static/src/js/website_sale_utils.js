odoo.define('website_decimal_quantity.utils', function (require) {
'use strict';

var utils = require('website_sale.utils');
var utilsDecimalQty = utils.updateCartNavBar;

/**
* This module overrides the updateCartNavBar function of the website_sale.utils module to provide
* support for decimal quantities in the cart.
* It replaces the cart quantity text with an animated icon and updates the cart summary and lines with the new data.
*/

utils.updateCartNavBar = function(data) {
    $(".my_cart_quantity")
        .parents('li.o_wsale_my_cart').removeClass('d-none').end()
        .addClass('o_mycart_zoom_animation').delay(300)
        .queue(function () {
            $(this)
                .toggleClass('fa fa-warning', !data.cart_quantity)
                .attr('title', data.warning)
                .text(data.cart_quantity || '')
                .removeClass('o_mycart_zoom_animation')
                .dequeue();
        });

    $(".js_cart_lines").first().before(data['website_sale.cart_lines']).end().remove();
    $(".js_cart_summary").replaceWith(data['website_sale.short_cart_summary']);
}
});
