/** @odoo-module */
import publicWidget from '@web/legacy/js/public/public_widget';
import utils from "@website_sale/js/website_sale_utils";
    /**
     * Custom implementation of the updateCartNavBar function.
     *
     * @param {Object} data - The data to update the cart navbar.
     */
    utils.updateCartNavBar = function (data) {
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
    $(".js_cart_summary").replaceWith(data['website_sale.short_cart_summary']);
    };
    return utils;
