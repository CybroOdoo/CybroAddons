/** @odoo-module **/

import { rpc } from '@web/core/network/rpc';
import { registry } from '@web/core/registry';
import { Interaction } from '@web/public/interaction';
import wSaleUtils from '@website_sale/js/website_sale_utils';
import wishlistUtils from '@website_sale_wishlist/js/website_sale_wishlist_utils';

export class WishlistToggle extends Interaction {
    static selector = '.o_add_wishlist_toggle';
    dynamicContent = {
        _root: { 't-on-click': this.toggleWishlist },
    };

    async toggleWishlist(ev) {
        const el = ev.currentTarget;
        const productId = parseInt(el.dataset.productProductId);
        if (!productId) return;

        const res = await this.waitFor(rpc('/shop/wishlist/toggle', { product_id: productId }));
        const iconEl = el.querySelector('.fa');
        
        if (res.action === 'added') {
            wishlistUtils.addWishlistProduct(productId);
            el.classList.add('o_in_wishlist');
            if (iconEl) {
                iconEl.classList.remove('fa-heart-o');
                iconEl.classList.add('fa-heart');
                iconEl.classList.add('text-danger');
            }
            // Animate flying clone
            const form = wSaleUtils.getClosestProductForm(el);
            await wSaleUtils.animateClone(
                $(document.querySelector('.o_wsale_my_wish')),
                $(document.querySelector('#product_detail_main') ?? el.closest('.o_cart_product') ?? form ?? el),
                25,
                40,
            );
        } else if (res.action === 'removed') {
            wishlistUtils.removeWishlistProduct(productId);
            el.classList.remove('o_in_wishlist');
            if (iconEl) {
                iconEl.classList.remove('fa-heart');
                iconEl.classList.remove('text-danger');
                iconEl.classList.add('fa-heart-o');
            }
        }
        wishlistUtils.updateWishlistNavBar();
    }
}

registry.category('public.interactions').add('theme_kids_care.wishlist_toggle', WishlistToggle);
