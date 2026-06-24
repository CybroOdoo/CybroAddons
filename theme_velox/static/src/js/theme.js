/** @odoo-module **/
import publicWidget from '@web/legacy/js/public/public_widget';
import { Component } from '@odoo/owl';

function veloxGetCsrf() {
    const m = document.querySelector('meta[name="csrf-token"], meta[name="csrf_token"]');
    return m ? (m.getAttribute('content') || m.getAttribute('value') || '') : '';
}

publicWidget.registry.VeloxTheme = publicWidget.Widget.extend({
    selector: '#wrapwrap',
    disabledInEditableMode: false,

    events: {
        'click #openSearchBtn': '_onOpenSearch',
        'click #closeSearchBtn': '_onCloseSearch',
        'click .velox-search-overlay': '_onOverlayClick',
        'click [data-velox-cart="1"]': '_onShopCartClick',
        'click .velox-card-cart-form .velox-grid-cart-btn': '_onHomeCartClick',
        'click .velox-card-img-wrap .o_add_wishlist': '_onWishlistClick',
    },

    start() {
        const sup = this._super(...arguments);
        this._navSticky();
        this._parallax();
        this._syncWishlistUI();
        
        // Bind escape key for search overlay
        this._onKeydown = this._onKeydown.bind(this);
        window.addEventListener('keydown', this._onKeydown);
        
        return sup;
    },

    destroy() {
        window.removeEventListener('keydown', this._onKeydown);
        this._super(...arguments);
    },

    // ── SEARCH OVERLAY ──

    _onOpenSearch(e) {
        if (this.editableMode) return;
        e.preventDefault();
        const overlay = this.el.querySelector('#searchOverlay');
        const input = this.el.querySelector('#searchInput');
        if (overlay) {
            overlay.classList.add('active');
            document.body.style.overflow = 'hidden';
            if (input) setTimeout(() => input.focus(), 200);
        }
    },

    _onCloseSearch(e) {
        if (this.editableMode) return;
        const overlay = this.el.querySelector('#searchOverlay');
        if (overlay) {
            overlay.classList.remove('active');
            document.body.style.overflow = '';
        }
    },

    _onOverlayClick(e) {
        if (this.editableMode) return;
        const overlay = this.el.querySelector('#searchOverlay');
        if (e.target === overlay) {
            this._onCloseSearch(e);
        }
    },

    _onKeydown(e) {
        if (this.editableMode) return;
        if (e.key === 'Escape') {
            this._onCloseSearch(e);
        }
    },

    // ── CART & WISHLIST HELPERS ──

    _showFeedback(btn, ok) {
        if (!btn) return;
        const icon = btn.querySelector('i');
        const saved = { cls: icon ? icon.className : '', bg: btn.style.background, color: btn.style.color };
        if (icon) icon.className = ok ? 'fa fa-check' : 'fa fa-times';
        btn.style.background = ok ? '#22c55e' : '#ef4444';
        btn.style.color = '#fff';
        setTimeout(() => {
            if (icon) icon.className = saved.cls;
            btn.style.background = saved.bg;
            btn.style.color = saved.color;
        }, 1400);
    },

    _setCartBadge(qty) {
        if (typeof qty !== 'number') return;
        this.el.querySelectorAll('.my_cart_quantity, .o_wsale_cart_badge, [data-cart-quantity]').forEach(el => {
            el.textContent = qty > 0 ? qty : '';
            el.classList.toggle('d-none', qty <= 0);
        });
    },

    async _cartAdd(templateId, productId, qty) {
        qty = qty || 1;
        const csrf = veloxGetCsrf();
        const r = await fetch('/shop/cart/add', {
            method: 'POST',
            credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
            body: JSON.stringify({
                jsonrpc: '2.0', method: 'call', id: Date.now(),
                params: {
                    product_template_id: parseInt(templateId || productId),
                    product_id: parseInt(productId),
                    quantity: qty
                },
            }),
        });
        if (!r.ok) throw new Error('HTTP ' + r.status);
        const d = await r.json();
        if (d.error) throw new Error(d.error.data ? d.error.data.message : 'cart error');
        return d.result;
    },

    async _wishlistAdd(templateId, productId) {
        const csrf = veloxGetCsrf();
        const r = await fetch('/shop/wishlist/add', {
            method: 'POST',
            credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
            body: JSON.stringify({
                jsonrpc: '2.0', method: 'call', id: Date.now(),
                params: {
                    product_id: productId ? parseInt(productId) : false,
                },
            }),
        });
        if (!r.ok) throw new Error('HTTP ' + r.status);
        const d = await r.json();
        if (d.error) throw new Error(d.error.data ? d.error.data.message : 'wishlist error');
        
        if (productId) {
            let ids = JSON.parse(sessionStorage.getItem('wishlist_product_ids') || '[]');
            let pid = parseInt(productId);
            if (!ids.includes(pid)) {
                ids.push(pid);
                sessionStorage.setItem('wishlist_product_ids', JSON.stringify(ids));
            }
        }
        
        return d.result;
    },

    async _checkConfigurator(templateId, productId) {
        try {
            const csrf = veloxGetCsrf();
            const r = await fetch('/website_sale/should_show_product_configurator', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
                body: JSON.stringify({
                    jsonrpc: '2.0', method: 'call', id: Date.now(),
                    params: {
                        product_template_id: parseInt(templateId),
                        ptav_ids: [],
                        is_product_configured: false
                    },
                }),
            });
            const d = await r.json();
            if (d.error) {
                console.error("Configurator check error:", d.error);
                return true; // Failsafe: if API fails or changes, always redirect to product page!
            }
            return d.result;
        } catch (e) {
            console.error("Configurator check failed:", e);
            return true; // Failsafe redirect
        }
    },

    // ── CLICK HANDLERS ──

    async _onShopCartClick(e) {
        if (this.editableMode) return;
        const btn = e.currentTarget;
        e.preventDefault();
        e.stopPropagation();

        const card = btn.closest('.oe_product_cart');
        if (!card) return;

        const nativeBtn = card.querySelector(
            '.o_wsale_product_action_row .o_wsale_product_btn_primary, ' +
            '.o_wsale_product_action_row a.btn-primary, ' +
            '.o_wsale_product_action_row button.btn-primary, ' +
            'a.o_wsale_product_btn_primary:not([data-velox-cart]), ' +
            'button.o_wsale_product_btn_primary:not([data-velox-cart])'
        );
        if (nativeBtn) {
            nativeBtn.click();
            this._showFeedback(btn, true);
            return;
        }

        const productId = btn.dataset.productProductId || btn.dataset.productTemplateId;
        const templateId = btn.dataset.productTemplateId || productId;
        if (!productId) return;

        const needsConfig = await this._checkConfigurator(templateId, productId);
        if (needsConfig) {
            const link = card.querySelector('a.oe_product_image_link');
            if (link) { window.location.href = link.href; return; }
        }

        btn.disabled = true;
        this._cartAdd(templateId, productId, 1).then(res => {
            this._setCartBadge(res && res.cart_quantity);
            this._showFeedback(btn, true);
        }).catch(() => {
            this._showFeedback(btn, false);
        }).finally(() => { setTimeout(() => { btn.disabled = false; }, 1500); });
    },

    async _onHomeCartClick(e) {
        if (this.editableMode) return;
        const btn = e.currentTarget;
        const form = btn.closest('.velox-card-cart-form');
        if (!form) return;

        e.preventDefault();
        e.stopPropagation();

        const productId = form.querySelector('input[name="product_id"]') &&
            form.querySelector('input[name="product_id"]').value;
        const templateId = form.querySelector('input[name="product_template_id"]') &&
            form.querySelector('input[name="product_template_id"]').value;
        if (!productId) { return; }

        if (Component.env && Component.env.services && Component.env.services.cart) {
            btn.disabled = true;
            try {
                await Component.env.services.cart.add({
                    productTemplateId: parseInt(templateId),
                    productId: productId ? parseInt(productId) : undefined,
                    quantity: 1,
                    ptavs: [],
                    isCombo: false,
                }, {
                    isBuyNow: false,
                    redirectToCart: false,
                    isConfigured: false,
                });
            } catch (err) {
                console.error("Cart add error", err);
            } finally {
                btn.disabled = false;
            }
            return;
        }

        const needsConfig = await this._checkConfigurator(templateId, productId);
        if (needsConfig) {
            const card = btn.closest('.velox-card') || btn.closest('article');
            if (card) {
                const link = card.querySelector('a.velox-card-img-link') || card.querySelector('a');
                if (link && link.href) { window.location.href = link.href; return; }
            }
            // fallback if link is not found
            window.location.href = `/shop/product/${templateId}`;
            return;
        }

        btn.disabled = true;
        this._cartAdd(templateId, productId, 1)
            .then(res => {
                this._setCartBadge(res && res.cart_quantity);
                this._showFeedback(btn, true);
            })
            .catch(() => {
                this._showFeedback(btn, false);
            })
            .finally(() => { setTimeout(() => { btn.disabled = false; }, 1500); });
    },

    _onWishlistClick(e) {
        if (this.editableMode) return;
        const btn = e.currentTarget;

        e.preventDefault();
        e.stopPropagation();

        if (btn.disabled || btn.classList.contains('o_in_wishlist')) return;

        const templateId = btn.dataset.productTemplateId;
        const productId = btn.dataset.productProductId;
        if (!templateId) return;

        btn.disabled = true;
        this._wishlistAdd(templateId, productId)
            .then(() => {
                btn.classList.add('o_in_wishlist');
                const icon = btn.querySelector('i');
                if (icon) { icon.classList.remove('fa-heart-o'); icon.classList.add('fa-heart'); }
            })
            .catch(err => {
                btn.disabled = false;
                const msg = (err && err.message) ? err.message.toLowerCase() : '';
                if (msg.includes('access') || msg.includes('login') || msg.includes('forbidden') || msg.includes('auth')) {
                    window.location.href = '/web/login?redirect=' + encodeURIComponent(window.location.pathname + window.location.search);
                } else {
                    this._showFeedback(btn, false);
                }
            });
    },

    // ── PUBLIC WIDGET HELPERS ──

    _navSticky() {
        const nav = this.el.querySelector('.velox-nav');
        if (!nav) return;
        const onScroll = () => nav.classList.toggle('velox-nav-scrolled', window.scrollY > 40);
        window.addEventListener('scroll', onScroll, { passive: true });
        onScroll();
    },

    _parallax() {
        const hero = this.el.querySelector('.s_velox_hero');
        if (!hero) return;
        if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
        if (window.matchMedia('(hover: none) and (pointer: coarse)').matches) return;
        if (window.innerWidth < 992) return;
        let ticking = false;
        window.addEventListener('scroll', () => {
            if (!ticking) {
                requestAnimationFrame(() => {
                    if (hero && hero.style) hero.style.backgroundPositionY = `calc(50% + ${window.scrollY * 0.25}px)`;
                    ticking = false;
                });
                ticking = true;
            }
        }, { passive: true });
    },
    
    _syncWishlistUI() {
        let ids = [];
        try {
            ids = JSON.parse(sessionStorage.getItem('wishlist_product_ids') || '[]');
        } catch (e) {}
        if (ids.length) {
            this.el.querySelectorAll('.o_add_wishlist, .o_add_wishlist_dyn, .velox-grid-wishlist-btn').forEach(btn => {
                const pid = parseInt(btn.dataset.productProductId);
                if (pid && ids.includes(pid)) {
                    btn.disabled = true;
                    btn.classList.add('disabled', 'o_in_wishlist');
                    const icon = btn.querySelector('.fa');
                    if (icon) {
                        icon.classList.remove('fa-heart-o');
                        icon.classList.add('fa-heart');
                    }
                }
            });
        }
    }
});
