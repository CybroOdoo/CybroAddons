/** @odoo-module **/
import { jsonrpc } from "@web/core/network/rpc_service";
import publicWidget from "@web/legacy/js/public/public_widget";
import animations from "@website/js/content/snippets.animation";
import wSaleUtils from "@website_sale/js/website_sale_utils";
import { Component } from "@odoo/owl";

publicWidget.registry.BestProduct = animations.Animation.extend({
    // To extend public widget
        selector: '.best_products_carousel',
        events: {
            'click .btn-add-to-cart': '_onClickAddToCart',
        },
         _onClickAddToCart: function (ev) {
            var $target = $(ev.currentTarget);
            var productId = $target.data('product-id');
            var self = this;
                 jsonrpc('/shop/cart/update_json', {
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
        start: async function ()  {
            var self = this;
            this._super.apply(this, arguments);
            await jsonrpc('/get_product_snippet', {}).then(function(data) {
                if (data) {
                    self.$target.empty().append(data);
                    self._initCarousel();
                }
            });
        },
        _initCarousel: function(autoplay = false, items = 4, slider_timing = 5000) {
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
                nav: true,
                navText: ['<i class="fa fa-angle-left" aria-hidden="false"></i>', '<i class="fa fa-angle-right" aria-hidden="false"></i>'],
                responsiveClass: true,
                responsive: {
                    0: {
                        items: 1,
                        nav: true
                    },
                    600: {
                        items: 2,
                        nav: true,
                    },
                    1000: {
                        items: 4,
                        nav: true,
                        loop: true,
                    }
                }
            });
        },
        counter: function() {
            var buttons = this.$('.owl-dots button');
            buttons.each(function(index, item) {});
        }
})
