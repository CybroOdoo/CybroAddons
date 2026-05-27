/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

publicWidget.registry.ReflectNewInWishlist = publicWidget.Widget.extend({
    selector: '#wrapwrap',
    events: {
        'click .reflect-newin-wishlist': '_onWishlistToggle',
        'click .reflect-newin-add-cart': '_onAddToCart',
    },

    async _refreshWishlistCounter() {
        try {
            const productIds = await rpc('/shop/wishlist/get_product_ids');
            const count = (productIds || []).length;
            this.el.querySelectorAll('.my_wish_quantity').forEach((node) => {
                node.textContent = `${count}`;
                node.classList.toggle('d-none', !count);
            });
        } catch {
            // Keep UI functional even if count refresh fails.
        }
    },

    async _onWishlistToggle(ev) {
        ev.preventDefault();
        const button = ev.currentTarget;
        const productId = parseInt(button.dataset.productProductId, 10);
        if (!productId || button.dataset.processing === '1') {
            return;
        }

        button.dataset.processing = '1';
        const icon = button.querySelector('i.fa');
        const inWishlist = button.classList.contains('o_in_wishlist');

        try {
            if (inWishlist) {
                await rpc('/shop/new/wishlist/remove', { product_id: productId });
                button.classList.remove('o_in_wishlist');
                if (icon) {
                    icon.classList.remove('fa-heart', 'text-danger');
                    icon.classList.add('fa-heart-o');
                }
            } else {
                await rpc('/shop/wishlist/add', { product_id: productId });
                button.classList.add('o_in_wishlist');
                if (icon) {
                    icon.classList.remove('fa-heart-o');
                    icon.classList.add('fa-heart', 'text-danger');
                }
            }
            await this._refreshWishlistCounter();
        } catch {
            // Ignore request errors, leave current state unchanged.
        } finally {
            button.dataset.processing = '0';
        }
    },

    _updateCartQuantity(quantity) {
        const value = `${quantity || 0}`;
        this.el.querySelectorAll('.o_wsale_cart_quantity').forEach((node) => {
            node.textContent = value;
        });
    },

    async _onAddToCart(ev) {
        ev.preventDefault();
        const button = ev.currentTarget;
        const productTemplateId = parseInt(button.dataset.productTemplateId, 10);
        const productId = parseInt(button.dataset.productProductId, 10);
        if (!productTemplateId || !productId || button.dataset.processing === '1') {
            return;
        }

        button.dataset.processing = '1';
        try {
            const data = await rpc('/shop/cart/add', {
                product_template_id: productTemplateId,
                product_id: productId,
                quantity: 1,
            });
            this._updateCartQuantity(data?.cart_quantity);
        } catch {
            // Ignore request errors, keep current cart display.
        } finally {
            button.dataset.processing = '0';
        }
    },
});
