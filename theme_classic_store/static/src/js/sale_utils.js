 odoo.define('website_sale.utils', function (require) {
'use strict';
    const wUtils = require('website.utils');
    /**
     * Mixin providing common functionality for handling cart updates.
     */
    const cartHandlerMixin = {
        /**
         * Determines whether to redirect after adding to cart or stay on the same page.
         */
        getRedirectOption() {
            const html = document.documentElement;
            this.stayOnPageOption = html.dataset.add2cartRedirect !== '0';
        },
        /**
         * Determines whether the "Buy Now" option was selected and gets the item image container.
         * @param {Event} ev - The event that triggered the cart update .
         */
        getCartHandlerOptions(ev) {
            this.isBuyNow = ev.currentTarget.classList.contains('o_we_buy_now');
            const targetSelector = ev.currentTarget.dataset.animationSelector || 'img';
            this.$itemImgContainer = this.$el.find('#product_detail_main');
        },
        /**
         * Adds a product to the cart.
         * @param {Object} params - The parameters for the cart update.
         * @returns {Promise} - A promise that resolves when the cart is updated.
         */
        addToCart(params) {
            if (this.isBuyNow) {
                params.express = true;
            } else if (this.stayOnPageOption) {
                return this._addToCartInPage(params);
            }
            return wUtils.sendRequest('/shop/cart/update', params);
        },
        /**
         * Adds a product to the cart on the same page.
         * @private
         * @param {Object} params - The parameters for the cart update.
         * @returns {Promise} - A promise that resolves when the cart is updated.
         */
        _addToCartInPage(params) {
            params.force_create = true;
            return this._rpc({
                route: "/shop/cart/update_json",
                params: params,
            }).then(async data => {
                await animateClone(this.$el.find('header .o_wsale_my_cart').first(), this.$itemImgContainer, 25, 40);
                updateCartNavBar(data);
            });
        },
    };

    /**
     * Animates the image of the product being added to the cart.
     * @param {jQuery} $cart - The cart element.
     * @param {jQuery} $elem - The element representing the product being added.
     * @param {number} offsetTop - The top offset of the animated image.
     * @param {number} offsetLeft - The left offset of the animated image.
     * @returns {Promise} - A promise that resolves when the animation is complete.
     */
    function animateClone($cart, $elem, offsetTop, offsetLeft) {
        $cart.find('.o_animate_blink').addClass('o_red_highlight o_shadow_animation').delay(500).queue(function () {
            $(this).removeClass("o_shadow_animation").dequeue();
        }).delay(2000).queue(function () {
            $(this).removeClass("o_red_highlight").dequeue();
        });
        return new Promise(function (resolve, reject) {
            var $imgtodrag = $elem.find('img').eq(0);
            if ($imgtodrag.length) {
                var $imgclone = $imgtodrag.clone()
                    .offset({
                        top: $imgtodrag.offset().top,
                        left: $imgtodrag.offset().left
                    })
                    .addClass('o_website_sale_animate')
                    .appendTo(document.body)
                    .css({
                        // Keep the same size on cloned img.
                        width: $imgtodrag.width(),
                        height: $imgtodrag.height(),
                    })
                    .animate({
                        top: 100,
                        left: 1400,
                        width: 75,
                        height: 75,
                    }, 1000, 'easeInOutExpo');

                $imgclone.animate({
                    width: 0,
                    height: 0,
                }, function () {
                    resolve();
                    $(this).detach();
                });
            } else {
                resolve();
            }
        });
    }

/**
 * Updates both navbar cart
 * @param {Object} data
 */
function updateCartNavBar(data) {
    var $qtyNavBar = $(".my_cart_quantity");
    _.each($qtyNavBar, function (qty) {
        var $qty = $(qty);
        $qty.parents('li:first').removeClass('d-none');
        $qty.addClass('o_mycart_zoom_animation').delay(300).queue(function () {
            $(this).text(data.cart_quantity);
            $(this).removeClass("o_mycart_zoom_animation").dequeue();
        });
    });
    $(".js_cart_lines").first().before(data['website_sale.cart_lines']).end().remove();
    $(".js_cart_summary").first().before(data['website_sale.short_cart_summary']).end().remove();
}
return {
    animateClone: animateClone,
    updateCartNavBar: updateCartNavBar,
    cartHandlerMixin: cartHandlerMixin,
};
});