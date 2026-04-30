/** @odoo-module */

import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";
import wSaleUtils from "@website_sale/js/website_sale_utils";

publicWidget.registry.get_product_tab = publicWidget.Widget.extend({
    selector: '.new_arrivals',

    events: {
        'click .o_add_wishlist': '_onClickAddWishlist',
    },

    init() {
        this._super(...arguments);
        this.wishlistProductIDs = JSON.parse(
            sessionStorage.getItem('website_sale_wishlist_product_ids') || '[]'
        );
    },

    start() {
        this._updateWishlistView();

        return rpc('/get_product_arrivals').then(data => {
            if (!data) return;

            this.$el.empty().append(data);

            this.$('#new_arrivals').owlCarousel({
                items: 4,
                loop: true,
                margin: 20,
                autoplay: true,
                autoplayTimeout: 3000,
                autoplayHoverPause: true,
                dots: false,
                nav: false,
                responsive: {
                    0: { items: 1 },
                    800: { items: 2 },
                    900: { items: 3 },
                    1000: { items: 4 },
                },
            });

            this._initializeWishlistButtons();
        });
    },

    _onClickAddWishlist(ev) {
        this._addNewProducts($(ev.currentTarget));
    },

    _initializeWishlistButtons() {
        this.$('.o_add_wishlist').each((_, el) => {
            const $el = $(el);
            const productId = parseInt($el.data('product-product-id'));
            if (this.wishlistProductIDs.includes(productId)) {
                $el.prop('disabled', true).addClass('disabled');
            }
        });
    },

    _addNewProducts($el) {
        const productID = $el.data('product-product-id');

        rpc('/shop/wishlist/add', { product_id: productID }).then(data => {
            if (!data) return;

            const $navButton = $('header .o_wsale_my_wish').first();

            this.wishlistProductIDs.push(productID);
            sessionStorage.setItem(
                'website_sale_wishlist_product_ids',
                JSON.stringify(this.wishlistProductIDs)
            );

            this._updateWishlistView();
            wSaleUtils.animateClone($navButton, $el.closest('form'), 25, 40);

            $el.prop('disabled', true).addClass('disabled');
        });
    },

    _updateWishlistView() {
        const $wishButton = $('.o_wsale_my_wish');
        if ($wishButton.hasClass('o_wsale_my_wish_hide_empty')) {
            $wishButton.toggleClass('d-none', !this.wishlistProductIDs.length);
        }
        $wishButton.find('.my_wish_quantity').text(this.wishlistProductIDs.length);
    },
});
