/** @odoo-module **/
/**
 * "Add" and wishlist buttons of the Petzen product cards ("Petzen Products"
 * snippet): same behaviour as the buttons of the
 * Odoo 18 shop product tiles, by reusing the standard website_sale widgets like
 * the dynamic product snippets of website_sale do.
 *   - "Add": WebsiteSale._handleAdd → product / combo configurator when needed,
 *     else added to the cart ("Add to Cart" website option: stay on the page
 *     with the cart notification, or go to the cart).
 *   - heart: ProductWishlist (website_sale_wishlist) → /shop/wishlist/add.
 */
import publicWidget from "@web/legacy/js/public/public_widget";
import { WebsiteSale } from "@website_sale/js/website_sale";
import "@website_sale_wishlist/js/website_sale_wishlist";

publicWidget.registry.PetzenProductCardCart = WebsiteSale.extend({
    selector: ".products-section",
    // only the card buttons: the shop / product page handlers of WebsiteSale
    // are not needed here
    events: {},
    read_events: {
        "click .product-card .add-btn[data-product-template-id]": "_onClickPetzenAdd",
    },

    /**
     * Like the dynamic product snippet cards of website_sale, the product page
     * logic of WebsiteSale.start() is skipped; only the "Add to Cart" website
     * option (stay on the page or go to the cart) is read.
     *
     * @override
     */
    start() {
        this.getRedirectOption();
    },

    /**
     * Add the product to the cart through the same form as a shop product tile.
     *
     * @private
     * @param {MouseEvent} ev
     */
    _onClickPetzenAdd(ev) {
        ev.preventDefault();
        const button = ev.currentTarget;
        const form = document.createElement("form");
        form.setAttribute("method", "post");
        form.setAttribute("action", "/shop/cart/update");
        for (const [name, value] of [
            ["product_template_id", button.dataset.productTemplateId],
            ["product_id", button.dataset.productId || ""],
        ]) {
            const input = document.createElement("input");
            input.setAttribute("type", "hidden");
            input.setAttribute("name", name);
            input.setAttribute("value", value);
            form.appendChild(input);
        }
        this.getCartHandlerOptions(ev);
        return this._handleAdd($(form)); // existing logic expects a jQuery form
    },
});

publicWidget.registry.PetzenProductCardWishlist = publicWidget.registry.ProductWishlist.extend({
    selector: ".products-section",
    events: {
        "click .product-card .o_add_wishlist": "_onClickAddWish",
    },

    /**
     * Inside the shop / product page the standard ProductWishlist widget
     * (.oe_website_sale) already handles the button.
     *
     * @override
     */
    _onClickAddWish(ev) {
        if (ev.currentTarget.closest(".oe_website_sale")) {
            return;
        }
        return this._super(...arguments);
    },

    /**
     * Also show the wishlist state on the hearts of the cards.
     *
     * @override
     */
    _updateWishlistView() {
        this._super(...arguments);
        this.el.querySelectorAll(".product-card .o_add_wishlist").forEach((heart) => {
            const inWishlist = this.wishlistProductIDs.includes(
                parseInt(heart.dataset.productProductId, 10)
            );
            if (!inWishlist) {
                return;
            }
            heart.disabled = true;
            heart.classList.add("pq-on");
            heart.setAttribute("aria-pressed", "true");
            heart.querySelector("iconify-icon")?.setAttribute("icon", "ri:heart-fill");
        });
    },
});
