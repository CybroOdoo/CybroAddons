import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";

export class WebsiteSaleCart extends Interaction {
    static selector = "#wrapwrap";

    dynamicContent = {
        ".cart-btn": { "t-on-click": this.addToCart },
//        ".wishlist-btn": { "t-on-click": this.addToWishlist },
//        ".subscribe-btn": { "t-on-click": this.onClickSubscribe },
    };

    /**
     * Add product to cart
     * @param {Event} ev - Click event
     */
    addToCart(ev) {
        ev.preventDefault();
        // Your cart logic here
        const productId = $(ev.currentTarget).data('product-id');
        const productTemplateId = $(ev.currentTarget).data('product-template-id');
        this.services.cart.add({
            productTemplateId: productTemplateId,
            productId: productId,

        }, {})

        console.log("Adding to cart:", productId, productTemplateId);
    }

    /**
     * Add product to wishlist
     * @param {Event} ev - Click event
     */
    addToWishlist(ev) {
        ev.preventDefault();
        // Your wishlist logic here
        const productId = ev.currentTarget.dataset.productId;
        console.log("Adding to wishlist:", productId);
    }

    /**
     * Handle newsletter subscription
     * @param {Event} ev - Click event
     */
    onClickSubscribe(ev) {
        ev.preventDefault();
        // Your subscription logic here
        console.log("Subscribing...");
    }
}

registry.category('public.interactions').add('theme_eco_food.add_to_cart', WebsiteSaleCart);

