/** @odoo-module **/
import { Interaction } from '@web/public/interaction';
import { registry } from '@web/core/registry';
import wishlistUtils from '@website_sale/js/wishlist_utils';

export class BeautyShop extends Interaction {
    static selector = '#wrapwrap';

    start() {
        this._initScrollEffects();
        this._initHeroPagination();
        this._initWishlistHandler();
        this._initCartQuantitySync();
        this._initClearCart();
    }

    destroy() {
        if (this._onScroll) {
            window.removeEventListener('scroll', this._onScroll);
        }
        if (this._heroInterval) {
            clearInterval(this._heroInterval);
        }
        if (this._cartObserver) {
            this._cartObserver.disconnect();
            this._cartObserver = null;
        }
    }

    /**
     * Initializes scroll-dependent UI changes, such as showing the
     * "Back to Top" button and updating the body class for header styling.
     * @private
     */
    _initScrollEffects() {
        const btt = this.el.querySelector('#backToTop');
        this._onScroll = () => {
            const y = window.scrollY;
            if (btt) {
                btt.classList.toggle('visible', y > 600);
            }
            document.body.classList.toggle('scrolled', y > 40);
        };
        window.addEventListener('scroll', this._onScroll, { passive: true });
        if (btt) {
            this.addListener(btt, 'click', (ev) => {
                ev.preventDefault();
                window.scrollTo({ top: 0, behavior: 'smooth' });
            });
        }
    }

    /**
     * Initializes the automatic pagination animation for the hero banner.
     * @private
     */
    _initHeroPagination() {
        const dots = this.el.querySelectorAll('.hero-pagination .dot');
        if (dots.length) {
            let active = 0;
            this._heroInterval = setInterval(() => {
                dots[active].classList.remove('active');
                active = (active + 1) % dots.length;
                dots[active].classList.add('active');
            }, 4200);
        }
    }

    /**
     * Handles wishlist button heart icon toggles on click and variant change.
     * @private
     */
    _initWishlistHandler() {
        this.addListener(this.el, 'click', (ev) => {
            const btn = ev.target.closest('.o_add_wishlist');
            if (btn) {
                setTimeout(() => {
                    btn.classList.add('active');
                    const icon = btn.querySelector('i');
                    if (icon) {
                        icon.classList.remove('bi-heart');
                        icon.classList.add('bi-heart-fill', 'text-danger');
                    }
                }, 100);
            }
        });

        this.addListener(this.el, 'product_changed', (ev) => {
            const btn = this.el.querySelector('.pd-wish.o_add_wishlist_dyn');
            if (btn && ev.detail?.productId) {
                const productId = parseInt(ev.detail.productId);
                const isWish = wishlistUtils.getWishlistProductIds().includes(productId);
                btn.disabled = isWish;
                btn.classList.toggle('active', isWish);
                const icon = btn.querySelector('i');
                if (icon) {
                    icon.classList.toggle('bi-heart-fill', isWish);
                    icon.classList.toggle('text-danger', isWish);
                    icon.classList.toggle('bi-heart', !isWish);
                }
            }
        });
    }

    /**
     * Keep cart hero count synchronized with navbar cart quantity updates.
     * @private
     */
    _initCartQuantitySync() {
        const cartBadge = document.querySelector('.bs_navigation .my_cart_quantity, li.o_wsale_my_cart .my_cart_quantity, .my_cart_quantity');
        const heroCount = this.el.querySelector('.cart-count .my_cart_quantity');
        if (cartBadge && heroCount) {
            this._cartObserver = new MutationObserver(() => {
                const qty = cartBadge.textContent.trim();
                const displayQty = qty || '0';
                if (heroCount.textContent !== displayQty) {
                    heroCount.textContent = displayQty;
                }
            });
            this._cartObserver.observe(cartBadge, {
                childList: true,
                characterData: true,
                subtree: true
            });
        }
    }

    /**
     * Synchronize navbar and hero badges immediately when clearing the cart.
     * @private
     */
    _initClearCart() {
        this.addListener(this.el, 'click', (ev) => {
            const btn = ev.target.closest('.clear-cart');
            if (btn) {
                try {
                    sessionStorage.removeItem('website_sale_cart_quantity');
                    sessionStorage.setItem('website_sale_cart_quantity', '0');
                } catch (e) {}
                const badges = document.querySelectorAll('.my_cart_quantity');
                badges.forEach((badge) => {
                    badge.textContent = '';
                    badge.classList.add('d-none');
                });
                const heroCount = this.el.querySelector('.cart-count .my_cart_quantity');
                if (heroCount) {
                    heroCount.textContent = '0';
                }
            }
        });
    }
}

registry.category('public.interactions').add('theme_beauty_shop.beauty_shop', BeautyShop);