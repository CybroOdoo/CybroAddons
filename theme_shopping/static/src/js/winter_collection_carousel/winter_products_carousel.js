import { registry } from '@web/core/registry';
import { rpc } from '@web/core/network/rpc';
import { renderToElement } from '@web/core/utils/render';
import { ShoppingCarousel } from '@theme_shopping/js/carousel';
import wSaleUtils from '@website_sale/js/website_sale_utils';
import wishlistUtils from '@website_sale/js/wishlist_utils';

export class WinterProduct extends ShoppingCarousel {
    static selector = '.winter_products_carousel';
    dynamicContent = {
        '.btn-add-to-cart': { 't-on-click.prevent': this.addToCart },
        '.st-add-wishlist': { 't-on-click.prevent': this.addToWishlist },
    };

    async willStart() {
        const products = await this.waitFor(rpc('/get_winter_product_snippet', {}));
        const originalChildren = [...this.el.childNodes];
        this.registerCleanup(() => this.el.replaceChildren(...originalChildren));
        this.el.replaceChildren(renderToElement('theme_shopping.winter_product_carousel_snippet', { products }));
    }

    start() {
        this.setupCarousel(this.el.querySelector('#product'));
    }

    async addToCart(ev) {
        const button = ev.currentTarget;
        if (button.dataset.busy) return;
        button.dataset.busy = '1';
        try {
            const result = await this.waitFor(rpc('/shop/cart/add', {
                product_template_id: Number(button.dataset.templateId),
                product_id: Number(button.dataset.productId),
                quantity: 1,
            }));
            wSaleUtils.updateCartNavBar(result);
            if (result.notification_info?.warning) {
                this.services.notification.add(result.notification_info.warning, { type: 'warning' });
            }
        } finally {
            delete button.dataset.busy;
        }
    }

    async addToWishlist(ev) {
        const button = ev.currentTarget;
        const productId = Number(button.dataset.productId);
        if (wishlistUtils.getWishlistProductIds().includes(productId)) return;
        button.disabled = true;
        try {
            await this.waitFor(rpc('/shop/wishlist/add', { product_id: productId }));
            wishlistUtils.addWishlistProduct(productId);
            wishlistUtils.updateWishlistNavBar();
        } catch (error) {
            button.disabled = false;
            throw error;
        }
    }
}

registry.category('public.interactions').add('theme_shopping.WinterProduct', WinterProduct);
