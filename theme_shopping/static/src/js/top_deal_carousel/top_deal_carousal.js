/** @odoo-module **/

import { rpc } from "@web/core/network/rpc";
import publicWidget from "@web/legacy/js/public/public_widget";
import { renderToElement } from "@web/core/utils/render";
import { loadCSS, loadJS } from "@web/core/assets";
import wSaleUtils from '@website_sale/js/website_sale_utils';
import { Component } from "@odoo/owl";
import { Interaction } from '@web/public/interaction';
import wishlistUtils from '@website_sale_wishlist/js/website_sale_wishlist_utils';



let owlAssetsPromise;

function ensureOwlAssets() {
    if (!owlAssetsPromise) {
        if (typeof window.$ !== "undefined" && $.fn.owlCarousel) {
            owlAssetsPromise = Promise.resolve();
        } else {
            owlAssetsPromise = Promise.all([
                loadCSS("/theme_shopping/static/src/css/owl.carousel.min.css"),
                loadCSS("/theme_shopping/static/src/css/owl.theme.default.min.css"),
                loadJS("/theme_shopping/static/src/js/owl.carousel.min.js"),
            ]);
        }
    }
    return owlAssetsPromise;
}

publicWidget.registry.BestProduct = publicWidget.Widget.extend({
    selector: '.best_deal_products_carousel',
    disabledInEditableMode: false,

    events: {
        'click .btn-add-to-cart': '_onClickAddToCart',
        'click .o_add_wishlist': '_onClickWishBtn',
    },

    start: function() {
        var self = this;
        return this._super.apply(this, arguments).then(function() {
            return ensureOwlAssets();
        }).then(function() {
            return rpc('/top_deal_product_snippet', {});
        }).then(function(data) {
            if (data) {
                self.$el.empty().html(renderToElement('theme_shopping.best_deal_product_carousel_snippet', { products: data }));
                self._initCarousel();
            }
        });
    },

    _initCarousel() {
        const $carousel = this.$el.find("#product");
        if ($carousel.length && $carousel.owlCarousel) {
            $carousel.owlCarousel({
                items: 3,
                loop: true,
                margin: 30,
                stagePadding: 30,
                smartSpeed: 450,
                autoplay: true,
                autoplayTimeout: 5000,
                autoplayHoverPause: true,
                dots: true,
                nav: false,
                responsive: {
                    0: { items: 1 },
                    600: { items: 2 },
                    1000: { items: 5 },
                },
            });
        }
    },

    async _onClickAddToCart(ev) {
        const $btn = $(ev.currentTarget);
        const productId = $btn.data('product-id');
        const productTemplateId = $btn.data('template-id');
        const fromSnippet = $btn.data('from-snippet');

        // Disable button during request
        $btn.prop('disabled', true);
        var originalText = $btn.text();
        $btn.text('Adding...');

        const result = await rpc('/shop/cart/add', {
            product_template_id: productTemplateId,
            product_id: productId,
            quantity: 1,
        });
        $btn.text('Added!');
        setTimeout(function () {
            $btn.text(originalText);
            $btn.prop('disabled', false);
        }, 1000);
        wSaleUtils.updateCartNavBar(result);
        wSaleUtils.showWarning(result.notification_info.warning);
    },

    async _onClickWishBtn(ev) {
        const $target = $(ev.currentTarget);
        const productId = $target.data('product-id');

        const result = await rpc('/shop/wishlist/add', { product_id: productId });
        if (result) {
            $('.o_wsale_my_wish').find('.my_wish_quantity').text(result[1]);
        }
    },

    onWillDestroy() {
        this._clearContent();
    },

    _clearContent() {
        const $area = this.$el.find('.best_deal_products_carousel');
        this.trigger_up('widgets_stop_request', { $target: $area });
        $area.html('');
    },
});
