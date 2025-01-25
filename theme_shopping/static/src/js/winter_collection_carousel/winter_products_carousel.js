/** @odoo-module **/
import {rpc } from "@web/core/network/rpc";
import publicWidget from "@web/legacy/js/public/public_widget";
import animations from "@website/js/content/snippets.animation";
import wSaleUtils from "@website_sale/js/website_sale_utils";
import { Component } from "@odoo/owl";
import { renderToElement } from "@web/core/utils/render";


publicWidget.registry.WinterProduct = animations.Animation.extend({
    // To extend public widget
    selector: '.winter_products_carousel',
     disabledInEditableMode: false,
    events: {
        'click .btn-add-to-cart': '_onClickAddToCart',
        'click .o_add_wishlist': '_onClickWishBtn'
    },
    //        Add to WishList
    _onClickWishBtn: function (ev) {
        var target = $(ev.currentTarget);
        var productId = target.data('product-id');
        const $wishButton = $('.o_wsale_my_wish');
        var $navButton = $('header .o_wsale_my_wish').first();

        rpc('/shop/wishlist/add', {
            'product_id': productId,
        }).then(function (result) {
            if (result) {
                $wishButton.find('.my_wish_quantity').text(result[1]);
            }
        })
    },
    //        Add to Cart
    _onClickAddToCart: function (ev) {
        var target = $(ev.currentTarget);
        var productId = target.data('product-id');
        var self = this;
        rpc('/shop/cart/update_json', {
            'product_id': productId,
            'add_qty': 1,
            display: false,
            force_create: true,
        }).then(async function (result) {
            wSaleUtils.updateCartNavBar(result);
            wSaleUtils.showWarning(result.notification_info.warning);
            wSaleUtils.showCartNotification(self.call.bind(self), result.notification_info);
            // Propagating the change to the express checkout forms
            Component.env.bus.trigger('cart_amount_changed', [result.amount, result.minor_amount])
        });
    },
    start: async function () {
        var self = this;
        this._super.apply(this, arguments);
        var data = await rpc('/get_winter_product_snippet', {})
        console.log("data",data)
            if (data) {
                this.$target.empty().html(renderToElement('theme_shopping.winter_product_carousel_snippet', {products: data}))
                self._initCarousel();
            }
    },
    _initCarousel: function (autoplay = false, items = 5, slider_timing = 5000) {
        var self = this;
        this.$("#product").owlCarousel({
            items: 3,
            loop: true,
            margin: 30,
            stagePadding: 30,
            smartSpeed: 450,
            autoplay: true,
            autoPlaySpeed: 1000,
            autoPlayTimeout: 1000,
            autoplayHoverPause: true,
            dots: true,
            nav: false,
            navText: ['<i class="fa fa-angle-left" aria-hidden="false"></i>', '<i class="fa fa-angle-right" aria-hidden="false"></i>'],
            responsiveClass: true,
            responsive: {
                0: {
                    items: 1,
                    nav: false,
                    loop: true
                },
                600: {
                    items: 2,
                    nav: false,
                    loop: true
                },
                1000: {
                    items: 5,
                    nav: false,
                    loop: true,
                }
            }
        });
    },
    counter: function () {
        var buttons = this.$('.owl-dots button');
        buttons.each(function (index, item) {});
    },

    destroy: function () {
        this._clearContent();
        this._super.apply(this, arguments);
    },

    _clearContent: function () {
        const $templateArea = this.$el.find('.winter_products_carousel');
        this.trigger_up('widgets_stop_request', {
            $target: $templateArea,
        });
        $templateArea.html('');
    },

})
