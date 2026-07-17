/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

publicWidget.registry.ReflectCartSidebar = publicWidget.Widget.extend({
    selector: '#wrapwrap',
    events: {
        'click #reflect_add_to_cart': '_onAddToCart',
        'click #products_grid .reflect-card-add-to-cart': '_onAddToCart',
        'click .reflect-cart-qty-minus': '_onUpdateQty',
        'click .reflect-cart-qty-plus': '_onUpdateQty',
        'click .reflect-remove-line': '_onRemoveLine',
        'click .reflect-cart-opener': '_onOpenCart',
        'click #reflect_cart_sidebar .btn-close': '_onCloseCart',
    },
    async _onOpenCart(ev) {
        ev.preventDefault();
        await this._refreshSidebar();
        this._showSidebar();
    },
    _onCloseCart(ev) {
        ev.preventDefault();
        if (this.bsOffcanvas) {
            this.bsOffcanvas.hide();
        } else {
            this._hideSidebar();
        }
    },
    /**
     * @override
     */
    start() {
        this.offcanvasElement = this.el.querySelector('#reflect_cart_sidebar');
        const Offcanvas = window.Offcanvas || (window.bootstrap && window.bootstrap.Offcanvas);
        if (this.offcanvasElement && Offcanvas) {
            this.bsOffcanvas = Offcanvas.getOrCreateInstance
                ? Offcanvas.getOrCreateInstance(this.offcanvasElement)
                : new Offcanvas(this.offcanvasElement);
        }
        return this._super.apply(this, arguments);
    },
    async _onAddToCart(ev) {
        ev.preventDefault();
        ev.stopPropagation();
        const form = ev.currentTarget.closest('form');
        const productId = parseInt(form.querySelector('input[name="product_id"]').value);
        const qtyInput = form.querySelector('input[name="add_qty"]');
        const quantity = parseFloat(qtyInput ? qtyInput.value : 1);
        if (!productId) {
            return;
        }
        try {
            const result = await rpc('/shop/cart/update_json', {
                product_id: productId,
                add_qty: quantity,
                display: false,
            });
            if (result.cart_quantity !== undefined) {
                this._setCartQuantity(result.cart_quantity);
            }
            await this._refreshSidebar();
            this._showSidebar();
        } catch (error) {
        }
    },
    async _onUpdateQty(ev) {
        ev.preventDefault();
        const btn = ev.currentTarget;
        const lineId = parseInt(btn.dataset.lineId);
        const productId = parseInt(btn.dataset.productId);
        const isPlus = btn.classList.contains('reflect-cart-qty-plus');
        try {
            await rpc('/shop/cart/update_json', {
                line_id: lineId,
                product_id: productId,
                set_qty: isPlus ? undefined : 0, // Placeholder if we wanted set_qty, but we'll use add_qty for simplicity
                add_qty: isPlus ? 1 : -1,
            });
            await this._refreshSidebar();
        } catch (error) {
        }
    },
    async _onRemoveLine(ev) {
        ev.preventDefault();
        const lineId = parseInt(ev.currentTarget.dataset.lineId);

        try {
            await rpc('/shop/cart/update_json', {
                line_id: lineId,
                set_qty: 0,
            });
            await this._refreshSidebar();
        } catch (error) {
        }
    },
    async _refreshSidebar() {
        try {
            const html = await rpc('/shop/cart/sidebar_html', {});
            const body = this.el.querySelector('#reflect_cart_sidebar_body');
            if (body) {
                body.innerHTML = html;
            }
            // Also update the navbar cart badge if it exists
            this._updateCartBadge();
        } catch (error) {
        }
    },
    _updateCartBadge() {
        rpc('/shop/cart/quantity', {}).then(qty => {
            this._setCartQuantity(qty || 0);
            // Update offcanvas title if it exists
            const title = this.el.querySelector('.reflect-offcanvas .offcanvas-title');
            if (title) {
                title.textContent = `Your Cart (${qty || 0})`;
            }
        });
    },
    _setCartQuantity(quantity) {
        const displayQty = quantity || 0;
        const badges = this.el.querySelectorAll('.o_wsale_cart_quantity');
        badges.forEach(badge => {
            badge.textContent = displayQty;
            badge.classList.toggle('d-none', !displayQty);
        });
    },
    _showSidebar() {
        if (!this.offcanvasElement) {
            return;
        }
        if (this.bsOffcanvas) {
            this.bsOffcanvas.show();
            return;
        }
        this.offcanvasElement.classList.add('show');
        this.offcanvasElement.style.visibility = 'visible';
        this.offcanvasElement.setAttribute('aria-modal', 'true');
        this.offcanvasElement.setAttribute('role', 'dialog');
        this.offcanvasElement.removeAttribute('aria-hidden');
        this.el.classList.add('modal-open');

        if (!this.el.querySelector('.offcanvas-backdrop.reflect-cart-backdrop')) {
            const backdrop = this.el.ownerDocument.createElement('div');
            backdrop.className = 'offcanvas-backdrop fade show reflect-cart-backdrop';
            backdrop.addEventListener('click', () => this._hideSidebar());
            this.el.appendChild(backdrop);
        }
    },
    _hideSidebar() {
        if (!this.offcanvasElement) {
            return;
        }
        this.offcanvasElement.classList.remove('show');
        this.offcanvasElement.style.visibility = 'hidden';
        this.offcanvasElement.setAttribute('aria-hidden', 'true');
        this.offcanvasElement.removeAttribute('aria-modal');
        this.offcanvasElement.removeAttribute('role');
        this.el.classList.remove('modal-open');
        this.el.querySelectorAll('.offcanvas-backdrop.reflect-cart-backdrop').forEach(el => el.remove());
    }
});
