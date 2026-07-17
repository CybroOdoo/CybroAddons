/** @odoo-module **/

import animations from "@website/js/content/snippets.animation";
import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

animations.registry.ReflectCategoryGrid = animations.Class.extend({
    selector: '.s_reflect_category_grid',
    start: function () {
        if (this.editableMode) {
            return;
        }
        this._loadCategories();
    },
    _loadCategories: function () {
        rpc('/theme_reflect/get_categories', {})
            .then((data) => {
                if (data) {
                    this.el.querySelector('.reflect-cat-grid-container').innerHTML = data;
                }
            });
    },
});
animations.registry.ReflectNewArrivals = animations.Class.extend({
    selector: '.s_reflect_new_arrivals',

    start: function () {
        if (this.editableMode) {
            return;
        }
        this._loadProducts();
    },
    _loadProducts: function () {
        var self = this;
        rpc('/theme_reflect/get_new_arrivals', {})
            .then((data) => {
                if (data) {
                    self.el.querySelector('.reflect-new-arrivals-container').innerHTML = data;
                    // Re-initialize wishlist widget on the newly injected content
                    self._bindWishlistButtons();
                }
            });
    },
    _bindWishlistButtons: function () {
        _attachWishlistHandlers(this.el);
    },
});
animations.registry.ReflectProductHighlight = animations.Class.extend({
    selector: '.s_reflect_product_highlight',
    start: function () {
        if (this.editableMode) {
            return;
        }
        this._loadProducts();
    },
    _loadProducts: function () {
        var self = this;
        rpc('/theme_reflect/get_product_highlight', {})
            .then((data) => {
                if (data) {
                    self.el.querySelector('.reflect-product-highlight-container').innerHTML = data;
                    // Re-initialize wishlist widget on the newly injected content
                    self._bindWishlistButtons();
                }
            });
    },
    _bindWishlistButtons: function () {
        _attachWishlistHandlers(this.el);
    },
});

function _attachWishlistHandlers(container) {
    // Load the current wishlist product IDs from session storage
    var wishlistProductIDs = JSON.parse(
        sessionStorage.getItem('website_sale_wishlist_product_ids') || '[]'
    );
    container.querySelectorAll('.o_add_wishlist').forEach(function (btn) {
        var productId = parseInt(btn.dataset.productProductId, 10);
        // If product already in wishlist, mark the button as disabled/active
        if (productId && wishlistProductIDs.includes(productId)) {
            btn.disabled = true;
            btn.classList.add('disabled', 'active');
            var icon = btn.querySelector('i');
            if (icon) {
                icon.classList.remove('fa-heart-o', 'text-dark');
                icon.classList.add('fa-heart', 'text-danger');
            }
        }

        // Attach click listener directly to the button
        if (!btn.dataset.wishlistBound) {
            btn.dataset.wishlistBound = 'true';
            btn.addEventListener('click', function (ev) {
                ev.preventDefault();
                ev.stopPropagation();

                if (btn.disabled || btn.classList.contains('disabled')) {
                    return;
                }

                var productId = parseInt(btn.dataset.productProductId, 10);

                if (!productId || isNaN(productId)) {
                    return;
                }
                // Disable button immediately to prevent double-click
                btn.disabled = true;
                btn.classList.add('disabled');

                // Visual feedback — fill the heart immediately
                var icon = btn.querySelector('i');
                if (icon) {
                    icon.classList.remove('fa-heart-o', 'text-dark');
                    icon.classList.add('fa-heart', 'text-danger');
                }
                btn.classList.add('active');

                // Make the RPC call to add to wishlist
                rpc('/shop/wishlist/add', {
                    product_id: productId,
                }).then(function () {
                    // Update session storage
                    var ids = JSON.parse(
                        sessionStorage.getItem('website_sale_wishlist_product_ids') || '[]'
                    );
                    if (!ids.includes(productId)) {
                        ids.push(productId);
                    }
                    sessionStorage.setItem('website_sale_wishlist_product_ids', JSON.stringify(ids));
                    // Update the wishlist count badge in the header
                    var badge = btn.ownerDocument.querySelector('header .my_wish_quantity');
                    if (badge) {
                        badge.textContent = ids.length;
                        badge.classList.remove('d-none');
                    }
                    // Also update wishlist link visibility
                    var wishLink = btn.ownerDocument.querySelector('header .o_wsale_my_wish');
                    if (wishLink && wishLink.classList.contains('d-none')) {
                        wishLink.classList.remove('d-none');
                    }
                }).catch(function (err) {
                    // On failure, revert the visual state
                    btn.disabled = false;
                    btn.classList.remove('disabled', 'active');
                    if (icon) {
                        icon.classList.remove('fa-heart', 'text-danger');
                        icon.classList.add('fa-heart-o', 'text-dark');
                    }
                });
            });
        }
    });
}
