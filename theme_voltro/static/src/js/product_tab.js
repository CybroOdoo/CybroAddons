/** @odoo-module */

import animations from "@website/js/content/snippets.animation";
import { rpc } from "@web/core/network/rpc";
import wSaleUtils from "@website_sale/js/website_sale_utils";
import VariantMixin from "@website_sale/js/sale_variant_mixin";

animations.registry.get_product_tab = animations.Class.extend({
    selector: '.new_arrivals',
    events: {
        'click .o_add_wishlist': '_onClickAddWishlist',
    },

    init: function () {
        this._super.apply(this, arguments);
        this.wishlistProductIDs = JSON.parse(sessionStorage.getItem('website_sale_wishlist_product_ids') || '[]');
    },
    onBuilt: function () {
        this.start();
    },
    onClone: function () {
        this.start();
    },
    start: function () {
        var self = this;
        this._updateWishlistView();
        rpc('/get_product_arrivals')
            .then(function (data) {
                self.$('.voltro_snippet_loader').remove();
                if (data) {
                    self.$target.empty().append(data);
                    self.$('#new_arrivals').owlCarousel({
                        items: 4,             // Show 6 items at a time
                        loop: true,           // Enable continuous loop mode
                        margin: 20,           // Space between items
                        autoplay: true,       // Enable auto scroll
                        autoplayTimeout: 3000, // Time interval for auto scroll (3 seconds)
                        autoplayHoverPause: true, // Pause on hover
                        dots: false,          // Disable dots
                        nav: false,            // Disable navigation arrows
                        responsive: {
                            0: { items: 1 },
                            800: { items: 2 },
                            900: { items: 3 },
                            1000: { items: 4 },
                        }
                    });
                    self._initializeWishlistButtons();

                }
            });
    },
    willStart: function () {
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

    _onClickAddWishlist: function (ev) {
        this._addNewProducts($(ev.currentTarget));
    },

    _initializeWishlistButtons: function () {
        var self = this;
        this.$('.o_add_wishlist').each(function () {
            var $el = $(this);
            var productId = parseInt($el.data('product-product-id'));
            if (self.wishlistProductIDs.includes(productId)) {
                $el.prop("disabled", true)
                    .addClass('disabled')
                    .attr('disabled', 'disabled');
            }
        });
    },

    _addNewProducts: function ($el) {
        var self = this;
        var productID = $el.data('product-product-id');
        rpc('/shop/wishlist/add', {
            product_id: productID,
        }).then(function (data) {
            if (data) {
                var $navButton = $('header .o_wsale_my_wish').first();
                self.wishlistProductIDs.push(productID);
                sessionStorage.setItem('website_sale_wishlist_product_ids', JSON.stringify(self.wishlistProductIDs));
                self._updateWishlistView();
                wSaleUtils.animateClone($navButton, $el.closest('form'), 25, 40);
                // It might happen that `onChangeVariant` is called at the same time as this function.
                // In this case we need to set the button to disabled again.
                // Do this only if the productID is still the same.
                let currentProductId = $el.data('product-product-id');
                if ($el.hasClass('o_add_wishlist_dyn')) {
                    currentProductId = parseInt($el.closest('.js_product').find('.product_id:checked').val());
                }
                if (productID === currentProductId) {
                    $el.prop("disabled", true).addClass('disabled');
                }
            }
        });
    },
    _updateWishlistView: function () {
        const $wishButton = $('.o_wsale_my_wish');
        if ($wishButton.hasClass('o_wsale_my_wish_hide_empty')) {
            $wishButton.toggleClass('d-none', !this.wishlistProductIDs.length);
        }
        $wishButton.find('.my_wish_quantity').text(this.wishlistProductIDs.length);
    },


});