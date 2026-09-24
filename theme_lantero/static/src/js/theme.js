/** @odoo-module **/
import { jsonrpc } from "@web/core/network/rpc_service";
import publicWidget from "@web/legacy/js/public/public_widget";

/**
 * Public widget for managing product carousels in the Lantero theme.
 * Handles smooth scrolling and navigation button state management.
 */
publicWidget.registry.LanteroSlider = publicWidget.Widget.extend({
    selector: '.s_products_carousel',
    events: {
        'click [data-slider-prev]': '_onPrevClick',
        'click [data-slider-next]': '_onNextClick',
    },
    /**
     * @override
     */
    start: function () {
        this.track = this.el.querySelector('[data-slider-track]');
        if (this.track) {
            this.track.addEventListener('scroll', this._updateButtons.bind(this), { passive: true });
            window.addEventListener('resize', this._updateButtons.bind(this));
            // Initialize button states after a short delay to ensure rendering is complete
            setTimeout(() => this._updateButtons(), 100);
        }
        return this._super.apply(this, arguments);
    },
    /**
     * Calculates the scroll step size based on the product card width and CSS gap.
     * @private
     * @returns {number} The step size in pixels.
     */
    _stepSize: function () {
        const card = this.track.querySelector('.product-card');
        if (!card) return this.track.clientWidth;
        const styles = window.getComputedStyle(this.track);
        const gap = parseFloat(styles.gap) || 24;
        return card.offsetWidth + gap;
    },
    /**
     * Updates the opacity and pointer events of navigation buttons based on scroll position.
     * Disables the 'previous' button at the start and the 'next' button at the end of the track.
     * @private
     */
    _updateButtons: function () {
        const prev = this.el.querySelector('[data-slider-prev]');
        const next = this.el.querySelector('[data-slider-next]');
        if (!this.track || (!prev && !next)) return;
        const scrollLeft = this.track.scrollLeft;
        const maxScroll = this.track.scrollWidth - this.track.clientWidth;
        if (prev) {
            prev.style.opacity = scrollLeft <= 5 ? '0.3' : '1';
            prev.style.pointerEvents = scrollLeft <= 5 ? 'none' : 'auto';
        }
        if (next) {
            next.style.opacity = scrollLeft >= (maxScroll - 5) ? '0.3' : '1';
            next.style.pointerEvents = scrollLeft >= (maxScroll - 5) ? 'none' : 'auto';
        }
    },
    /**
     * Handles the 'previous' button click event by scrolling the track to the left.
     * @private
     * @param {Event} ev
     */
    _onPrevClick: function (ev) {
        ev.preventDefault();
        this.track.scrollBy({ left: -this._stepSize(), behavior: 'smooth' });
    },
    /**
     * Handles the 'next' button click event by scrolling the track to the right.
     * @private
     * @param {Event} ev
     */
    _onNextClick: function (ev) {
        ev.preventDefault();
        this.track.scrollBy({ left: this._stepSize(), behavior: 'smooth' });
    },
});

publicWidget.registry.LanteroWishlist = publicWidget.Widget.extend({
    selector: 'body',
    events: {
        'click .lantero-shop-page .o_add_wishlist': '_onWishlistClick',
        'click .s_products_carousel .o_add_wishlist': '_onWishlistClick',
    },

    /**
     * Adds products to the wishlist from Lantero cards without relying on the
     * core delegated handler, which can miss these customized card layouts.
     *
     * @private
     * @param {Event} ev
     */
    _onWishlistClick: async function (ev) {
        ev.preventDefault();
        ev.stopPropagation();
        ev.stopImmediatePropagation();

        const button = ev.currentTarget;
        if (button.disabled || button.classList.contains('disabled')) {
            return;
        }

        const form = button.closest('form');
        const productInput = form && form.querySelector('input.product_id');
        const productId = parseInt(button.dataset.productProductId || productInput?.value, 10);
        if (!productId) {
            return;
        }

        button.disabled = true;
        button.classList.add('disabled');

        try {
            await jsonrpc('/shop/wishlist/add', { product_id: productId });
            this._rememberWishlistProduct(productId);
            this._updateWishlistHeader();
        } catch (error) {
            button.disabled = false;
            button.classList.remove('disabled');
            throw error;
        }
    },

    /**
     * @private
     * @param {number} productId
     */
    _rememberWishlistProduct: function (productId) {
        const storageKey = 'website_sale_wishlist_product_ids';
        const productIds = JSON.parse(sessionStorage.getItem(storageKey) || '[]');
        if (!productIds.includes(productId)) {
            productIds.push(productId);
            sessionStorage.setItem(storageKey, JSON.stringify(productIds));
        }
    },

    /**
     * @private
     */
    _updateWishlistHeader: function () {
        const wishLink = document.querySelector('header .o_wsale_my_wish');
        const quantity = wishLink && wishLink.querySelector('.my_wish_quantity');
        if (!wishLink || !quantity) {
            return;
        }

        const productIds = JSON.parse(sessionStorage.getItem('website_sale_wishlist_product_ids') || '[]');
        quantity.textContent = productIds.length;
        wishLink.classList.remove('d-none');
    },
});

if (publicWidget.registry.subscribe) {
    publicWidget.registry.subscribe.include({
        /**
         * Keep Lantero's footer newsletter field empty instead of showing the
         * email returned by the subscriber lookup.
         *
         * @override
         * @param {Object} data
         */
        _updateView: function (data) {
            const inputEl = this.el.querySelector('input.js_subscribe_value, input.js_subscribe_email');
            const previousValue = inputEl && inputEl.value;

            this._super.apply(this, arguments);

            if (
                this.el.dataset.lanteroEmptyEmail &&
                inputEl &&
                !data.is_subscriber &&
                (!previousValue || previousValue === data.value)
            ) {
                inputEl.value = '';
            }
        },
    });
}
