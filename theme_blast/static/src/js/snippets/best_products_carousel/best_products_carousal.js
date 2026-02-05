/** @odoo-module **/

import { rpc } from "@web/core/network/rpc";
import publicWidget from "@web/legacy/js/public/public_widget";
import wSaleUtils from "@website_sale/js/website_sale_utils";
import { Component } from "@odoo/owl";

/**
 * Widget: BestProduct
 * Description:
 *   - Handles the Best Products carousel snippet.
 *   - Loads products dynamically via RPC from /get_product_snippet.
 *   - Initializes Owl Carousel.
 *   - Handles add-to-cart functionality with live cart updates and notifications.
 */

publicWidget.registry.BestProduct = publicWidget.Widget.extend({
    selector: '.best_products_carousel',
    events: {
        'click .btn-add-to-cart': '_onClickAddToCart',
    },

    async start() {
        this._super.apply(this, arguments);
        const data = await rpc('/get_product_snippet', {});
        if (data) {
            this.$target.empty().append(data);
            this._initCarousel();
        }
    },

    _onClickAddToCart(ev) {
        const $target = $(ev.currentTarget);
        const productId = $target.data('product-id');
        rpc('/shop/cart/update', {
            product_id: productId,
            add_qty: 1,
            display: false,
            force_create: true,
        }).then((result) => {
            const hasCart = document.querySelector('.o_wsale_my_cart, .o_wsale_my_cart_icon, .o_wsale_topbar, .o_wsale_cart_navbar');
            if (hasCart) {
                wSaleUtils.updateCartNavBar(result);
            }
            wSaleUtils.showCartNotification(this.call.bind(this), result.notification_info);
            Component.env.bus.trigger('cart_amount_changed', [result.amount, result.minor_amount]);
        });
    },

    _initCarousel(autoplay = false, items = 4, slider_timing = 5000) {
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
            navText: [
                '<i class="fa fa-angle-left" aria-hidden="false"></i>',
                '<i class="fa fa-angle-right" aria-hidden="false"></i>'
            ],
            responsive: {
                0: { items: 1, nav: true },
                600: { items: 2, nav: true },
                1000: { items: 4, nav: true, loop: true },
            },
        });
    },
});
