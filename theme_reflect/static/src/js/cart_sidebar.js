/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";

publicWidget.registry.ReflectCartSidebar = publicWidget.Widget.extend({
    selector: '#wrapwrap',
    events: {
        'click #reflect_add_to_cart': '_onAddToCart',
        'click .reflect-add-to-cart-btn': '_onShopCardAddToCart',
        'click .reflect-cart-qty-minus': '_onUpdateQty',
        'click .reflect-cart-qty-plus': '_onUpdateQty',
        'click .reflect-remove-line': '_onRemoveLine',
        'click .reflect-cart-opener': '_onOpenCart',
    },

    async _onOpenCart(ev) {
        ev.preventDefault();
        await this._refreshSidebar();
        if (this.bsOffcanvas) {
            this.bsOffcanvas.show();
        }
    },

    /**
     * @override
     */
    start() {
        this.offcanvasElement = document.getElementById('reflect_cart_sidebar');
        const Offcanvas = window.bootstrap && window.bootstrap.Offcanvas || window.Offcanvas;
        if (this.offcanvasElement && Offcanvas) {
            this.bsOffcanvas = new Offcanvas(this.offcanvasElement);
        }
        return this._super.apply(this, arguments);
    },

    /**
     * Handle "Add to Cart" button on the product detail page (#reflect_add_to_cart).
     * Submits the form normally so Odoo's setting (stay/go to cart/dialog) is respected.
     */
    async _onAddToCart(ev) {
        ev.preventDefault();
        const $form = $(ev.currentTarget).closest('form');
        const productId = parseInt($form.find('input[name="product_id"]').val());
        const quantity = parseFloat($form.find('input[name="add_qty"]').val() || 1);

        if (!productId) {
            return;
        }

        try {
            await jsonrpc('/shop/cart/update_json', {
                product_id: productId,
                add_qty: quantity,
            });
            await this._refreshSidebar();
            if (this.bsOffcanvas) {
                this.bsOffcanvas.show();
            }
        } catch (error) {
            console.error("Add to cart failed", error);
        }
    },

    /**
     * Handle the shop product card cart button (.reflect-add-to-cart-btn).
     * Reads the Odoo "Add to Cart" website setting and acts accordingly:
     *   - 'stay'   → add via JSON, open sidebar
     *   - 'go_to_cart' → add via JSON, redirect to /shop/cart
     *   - 'dialog' → submit the parent form normally (Odoo handles the dialog)
     */
    async _onShopCardAddToCart(ev) {
        ev.preventDefault();
        ev.stopPropagation();

        const $btn = $(ev.currentTarget);
        const productId = parseInt($btn.data('product-id'));
        const $form = $btn.closest('form');

        if (!productId) {
            // Fallback: submit the form normally
            $form[0] && $form[0].submit();
            return;
        }

        // Read Odoo's "Add to Cart" action setting from the page
        // Odoo renders it as a data attribute on #wrapwrap or we detect via
        // the website_sale JS global config if available.
        const cartAction = this._getCartAction();

        if (cartAction === 'go_to_cart') {
            try {
                await jsonrpc('/shop/cart/update_json', {
                    product_id: productId,
                    add_qty: 1,
                });
                window.location.href = '/shop/cart';
            } catch (error) {
                console.error("Add to cart failed", error);
            }
        } else if (cartAction === 'dialog') {
            // Let Odoo's native form submit handle the dialog
            $form[0] && $form[0].submit();
        } else {
            // Default: 'stay' — add via JSON and open the sidebar
            try {
                await jsonrpc('/shop/cart/update_json', {
                    product_id: productId,
                    add_qty: 1,
                });
                await this._refreshSidebar();
                if (this.bsOffcanvas) {
                    this.bsOffcanvas.show();
                }
            } catch (error) {
                console.error("Add to cart failed", error);
            }
        }
    },

    /**
     * Detect Odoo's "Add to Cart" setting.
     * Odoo 17 exposes it on the website_sale JS module config, or we fall back
     * to reading a data attribute injected on #wrapwrap by layout.xml.
     */
    _getCartAction() {
        // Method 1: Odoo 17 website_sale exposes cart redirect via global config
        try {
            const cfg = odoo.__DEBUG__.services['website_sale.cart_redirect'] ||
                        odoo.__DEBUG__.services['website_sale.add_to_cart_redirect'];
            if (cfg) return cfg;
        } catch (e) { /* not available */ }

        // Method 2: data attribute on wrapwrap (set by layout.xml t-att-data-cart-action)
        const wrapwrap = document.getElementById('wrapwrap');
        if (wrapwrap) {
            const action = wrapwrap.dataset.cartAction;
            if (action) return action;
        }

        // Method 3: check if Odoo's o_website_sale_cart_redirect_url meta tag exists
        const meta = document.querySelector('meta[name="cart_redirect_after_add"]');
        if (meta) {
            const val = meta.getAttribute('content');
            if (val === '1' || val === 'true') return 'go_to_cart';
        }

        return 'stay';
    },

    async _onUpdateQty(ev) {
        ev.preventDefault();
        const $btn = $(ev.currentTarget);
        const lineId = parseInt($btn.data('line-id'));
        const productId = parseInt($btn.data('product-id'));
        const isPlus = $btn.hasClass('reflect-cart-qty-plus');

        try {
            await jsonrpc('/shop/cart/update_json', {
                line_id: lineId,
                product_id: productId,
                set_qty: isPlus ? undefined : 0,
                add_qty: isPlus ? 1 : -1,
            });
            await this._refreshSidebar();
        } catch (error) {
            console.error("Update qty failed", error);
        }
    },

    async _onRemoveLine(ev) {
        ev.preventDefault();
        const $btn = $(ev.currentTarget);
        const lineId = parseInt($btn.data('line-id'));
        const productId = parseInt($btn.data('product-id'));

        try {
            await jsonrpc('/shop/cart/update_json', {
                line_id: lineId,
                product_id: productId,
                set_qty: 0,
            });
            await this._refreshSidebar();
        } catch (error) {
            console.error("Remove line failed", error);
        }
    },

    async _refreshSidebar() {
        try {
            const html = await jsonrpc('/shop/cart/sidebar_html', {});
            const $body = $('#reflect_cart_sidebar_body');
            if ($body.length) {
                $body.html(html);
            }
            this._updateCartBadge();
        } catch (error) {
            console.error("Refresh sidebar failed", error);
        }
    },

    _updateCartBadge() {
        const $badge = $('.o_wsale_cart_quantity');
        jsonrpc('/shop/cart/quantity', {}).then(qty => {
            const displayQty = qty || 0;
            if ($badge.length) {
                $badge.text(displayQty).toggleClass('d-none', !qty);
            }
            const $title = $('.reflect-offcanvas .offcanvas-title');
            if ($title.length) {
                $title.text(`Your Cart (${displayQty})`);
            }
        });
    }
});