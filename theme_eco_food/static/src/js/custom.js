/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";
import wSaleUtils from "@website_sale/js/website_sale_utils";

publicWidget.registry.WebsiteSaleCart = publicWidget.Widget.extend({
    selector: '#wrapwrap',
    events: {
        'click .cart-btn': '_addToCart',
        'click .wishlist-btn': '_addToWishlist',
        'click .subscribe-btn': 'onClickSubscribe',
    },
    init() {
        this._super(...arguments);
        this.wishlistProductIDs = JSON.parse(sessionStorage.getItem('website_sale_wishlist_product_ids') || '[]');
    },
    willStart() {
        var self = this;
        var def = this._super.apply(this, arguments);
        var wishDef;
        if (this.wishlistProductIDs.length != +$('header#top .my_wish_quantity').text()) {
            wishDef = $.get('/shop/wishlist', {
                count: 1,
            }).then(function (res) {
                self.wishlistProductIDs = JSON.parse(res);
                sessionStorage.setItem('website_sale_wishlist_product_ids', res);
            });
        }
        return Promise.all([def, wishDef]);
    },
    start() {
        this._updateWishlistView();
    },
    async _addToCart(ev) {
        // Function for adding products to cart.
        let productId = $(ev.currentTarget).data('product-id');
        let data = await jsonrpc("/shop/cart/update_json", {
            add_qty: 1,
            product_id: productId
        });
        wSaleUtils.updateCartNavBar(data);
    },
    async _addToWishlist(ev) {
        // Function for adding products to wishlist.
        let productId = $(ev.currentTarget).data('product-id');
        let data = await jsonrpc('/shop/wishlist/add', {
            product_id: productId,
            is_template: true
        });
        if (data) {
            this.wishlistProductIDs.push(productId);
            sessionStorage.setItem('website_sale_wishlist_product_ids', JSON.stringify(this.wishlistProductIDs));
            this._updateWishlistView();
        }
    },
    _updateWishlistView () {
        // Function to update wishlist count in website.
        const $wishButton = $('.o_wsale_my_wish');
        if ($wishButton.hasClass('o_wsale_my_wish_hide_empty')) {
            $wishButton.toggleClass('d-none', !this.wishlistProductIDs.length);
        }
        $wishButton.find('.my_wish_quantity').text(this.wishlistProductIDs.length);
    },
    async onClickSubscribe(ev) {
        // Function for subscribe newsletter.
        const $button = $(ev.currentTarget);
        const $input = $(ev.currentTarget.parentElement).find('input');
        this.$el.removeClass('o_has_error').find('.form-control').removeClass('is-invalid');
        if ($input.val().match(/.+@.+/)) {
            let data = await jsonrpc('/subscribe_newsletter', {
                email: $input.val()
            });
            if (data) {
                $(ev.currentTarget.parentElement.parentElement).find('.warning').hide();
                $input.css('pointer-events', 'none');
                $button.css('background-color', 'green !important');
                $button.text("THANKS");
            } else {
                $(ev.currentTarget.parentElement.parentElement).find('.warning').text("Already subscribed to the newsletter.");
                $(ev.currentTarget.parentElement.parentElement).find('.warning').show();
            }
        } else {
            this.$el.addClass('o_has_error').find('.form-control').addClass('is-invalid');
            $(ev.currentTarget.parentElement.parentElement).find('.warning').text("Enter a valid email.");
            $(ev.currentTarget.parentElement.parentElement).find('.warning').show();
        }
    },
})