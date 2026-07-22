/** @odoo-module **/

import publicWidget from '@web/legacy/js/public/public_widget';

publicWidget.registry.VeloxTheme = publicWidget.Widget.extend({
    selector: '#wrapwrap',
    disabledInEditableMode: false,

    events: {
        'click #openSearchBtn': '_onOpenSearch',
        'click #closeSearchBtn': '_onCloseSearch',
        'click .velox-search-overlay': '_onOverlayClick',
        'click .velox-snippet-add-to-cart-btn': '_onAddToCartClick',
    },

    start() {
        const sup = this._super(...arguments);
        this.rpc = this.bindService("rpc");
        this._onKeydown = this._onKeydown.bind(this);
        this.$searchOverlay = this.$el.find('#searchOverlay');
        this.$searchInput = this.$el.find('#searchInput');
        this.$cartQuantity = this.$el.find('.my_cart_quantity');
        window.addEventListener('keydown', this._onKeydown);
        return sup;
    },

    destroy() {
        window.removeEventListener('keydown', this._onKeydown);
        this._super(...arguments);
    },

    /** Open search overlay. */
    _onOpenSearch(ev) {
        if (this.editableMode) return;
        ev.preventDefault();
        if (!this.$searchOverlay.length) return;
        this.$searchOverlay.addClass('active');
        $('body').css('overflow', 'hidden');
        if (this.$searchInput.length) {
            setTimeout(() => this.$searchInput.trigger('focus'), 200);
        }
    },

    /** Close search overlay. */
    _onCloseSearch() {
        if (this.editableMode) return;
        if (this.$searchOverlay.length) {
            this.$searchOverlay.removeClass('active');
        }
        $('body').css('overflow', '');
    },

    /** Close overlay on outside click. */
    _onOverlayClick(ev) {
        if (this.editableMode) return;
        if ($(ev.target).is(this.$searchOverlay)) {
            this._onCloseSearch();
        }
    },
    /** Close search on escape key. */
    _onKeydown(ev) {
        if (this.editableMode) return;
        if (ev.key === 'Escape') {
            this._onCloseSearch();
        }
    },
    /** add to cart. */
    _onAddToCartClick(ev) {
        if (this.editableMode) return;
        ev.preventDefault();
        ev.stopPropagation();
        const $btn = $(ev.currentTarget);
        if ($btn.data('adding-to-cart')) return;
        $btn.data('adding-to-cart', true);
        $btn.prop('disabled', true);
        const $container = $btn.closest('.velox-add-to-cart-form');
        if (!$container.length) {
            this._resetButton($btn);
            return;
        }
        const productId = parseInt($container.find('input[name="product_id"]').val(), 10);
        if (!productId) {
            this._resetButton($btn);
            return;
        }
        this.rpc('/shop/cart/update_json', {
            product_id: productId,
            add_qty: 1,
            display: false,
        }).then(data => {
            if (!data || data.cart_quantity === undefined) {
                this._resetButton($btn);
                return;
            }
            this.$cartQuantity.text(data.cart_quantity).removeClass('d-none');
            const originalContent = $btn.html();
            $btn.html(`
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">
                    <path fill="currentColor" d="m10 15.17l-3.42-3.42l-1.41 1.41L10 18l8-8l-1.41-1.41z"/>
                </svg>
            `);
            $btn.css({backgroundColor: 'var(--velox-accent)', color: '#fff'});
            setTimeout(() => {
                $btn.html(originalContent);
                $btn.css({backgroundColor: '', color: ''});
                this._resetButton($btn);
            }, 1500);
        }).catch(() => {
            this._resetButton($btn);
        });
    },
    /** Reset add to cart button. */
    _resetButton($btn) {
        $btn.data('adding-to-cart', false);
        $btn.prop('disabled', false);
    },
});