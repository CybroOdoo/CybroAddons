/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.ThemeVelora = publicWidget.Widget.extend({
    selector: '#wrapwrap',
    disabledInEditableMode: false,

    events: {
        'click #backToTop': '_onBackToTopClick',
        'click #hamburger': '_onHamburgerClick',
        'click #mobileMenuClose': '_onMobileMenuClose',
        'click .mobile-menu a': '_onMobileMenuClose',
        'click #searchToggle': '_onSearchToggle',
        'click #searchClose': '_onSearchClose',
        'click #searchOverlay': '_onSearchOverlayClick',
        'click #cartToggle': '_onCartToggle',
        'click #cartToggleMobile': '_onCartToggleMobile',
        'click #cartClose': '_onCartClose',
        'click #drawerBackdrop': '_onCartClose',
        'click #wishlistToggleMobile': '_onMobileMenuClose',
        'click .category-card': '_onCategoryCardClick',
        'click .wishlist-btn[data-product-product-id]:not(.o_add_wishlist)': '_onWishlistBtnClick',
        'click .collection-card, .collections-page-card': '_onCollectionCardClick',
        'click .accordion-header': '_onAccordionHeaderClick',
        'submit #newsletterForm': '_onNewsletterSubmit',
        'submit #contactForm': '_onContactSubmit',
        'submit #contactus_form': '_onContactSubmit',
        'submit form[action="/shop/cart/update"]': '_onCartFormSubmit',
        'click .add-cart-btn, .shop-add-cart-btn': '_onAddCartBtnClick',
        'click .o_add_wishlist': '_onOdooWishlistBtnClick',
        'click a': '_onCollectionsLinkClick',
        'click .velora-wishlist-page .o_wish_add': '_onWishlistPageAddCartClick',
        'click #userMenuButton': '_onUserMenuButtonClick',
    },

    /**
     * @override
     */
    start() {
        this._super(...arguments);
        if (this.editableMode) return Promise.resolve();

        this.toastTimer = null;
        this.autoplayTimer = null;

        this._initScrollState();
        this._initGlobalKeydown();
        this._initWishlistBtns();
        this._initScrollReveal();
        this._initCountUpStats();
        this._initTestimonialCarousel();
        this._initFooterYear();
        this._initUserDropdownDismiss();
        this._initSearchResultsHeader();
        this._initContactFormValidation();

        return Promise.resolve();
    },

    /* ============ UTILITY & HELPER METHODS ============ */

    showToast(message) {
        const toast = this.el.querySelector('#toast') || document.querySelector('#toast');
        if (!toast) return;
        toast.textContent = message;
        toast.classList.add('show');
        clearTimeout(this.toastTimer);
        this.toastTimer = setTimeout(() => toast.classList.remove('show'), 2600);
    },

    async jsonRpc(route, params = {}) {
        const response = await fetch(route, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ jsonrpc: '2.0', method: 'call', params, id: Math.floor(performance.now()) }),
        });
        const payload = await response.json();
        if (payload.error) {
            throw new Error(payload.error.data?.message || 'Request failed');
        }
        return payload.result;
    },

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text == null ? '' : String(text);
        return div.innerHTML;
    },

    /* ============ SCROLL STATE ============ */

    _initScrollState() {
        const scrollProgress = this.el.querySelector('#scrollProgress') || document.querySelector('#scrollProgress');
        const siteHeader = this.el.querySelector('#siteHeader') || document.querySelector('#siteHeader');
        const backToTop = this.el.querySelector('#backToTop') || document.querySelector('#backToTop');

        const onScroll = () => {
            if (this.editableMode) return;
            const scrollTop = window.scrollY;
            const docHeight = document.documentElement.scrollHeight - window.innerHeight;
            const progress = docHeight > 0 ? (scrollTop / docHeight) * 100 : 0;
            if (scrollProgress) scrollProgress.style.width = `${progress}%`;

            if (scrollTop > 60) {
                siteHeader?.classList.add('scrolled');
            } else {
                siteHeader?.classList.remove('scrolled');
            }

            if (scrollTop > 500) {
                backToTop?.classList.add('show');
            } else {
                backToTop?.classList.remove('show');
            }
        };

        window.addEventListener('scroll', onScroll, { passive: true });
        onScroll();
    },

    _onBackToTopClick(e) {
        if (this.editableMode) return;
        e.preventDefault();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    },

    /* ============ MOBILE MENU ============ */

    _closeMobileMenu() {
        const hamburger = this.el.querySelector('#hamburger') || document.querySelector('#hamburger');
        const mobileMenu = this.el.querySelector('#mobileMenu') || document.querySelector('#mobileMenu');
        hamburger?.classList.remove('active');
        hamburger?.setAttribute('aria-expanded', 'false');
        mobileMenu?.classList.remove('active');
    },

    _onHamburgerClick(e) {
        if (this.editableMode) return;
        e.preventDefault();
        const hamburger = e.currentTarget;
        const mobileMenu = this.el.querySelector('#mobileMenu') || document.querySelector('#mobileMenu');
        const isActive = hamburger.classList.toggle('active');
        hamburger.setAttribute('aria-expanded', String(isActive));
        mobileMenu?.classList.toggle('active', isActive);
    },

    _onMobileMenuClose() {
        this._closeMobileMenu();
    },

    /* ============ SEARCH OVERLAY ============ */

    _openSearch() {
        if (this.editableMode) return;
        const searchOverlay = this.el.querySelector('#searchOverlay') || document.querySelector('#searchOverlay');
        const searchToggle = this.el.querySelector('#searchToggle') || document.querySelector('#searchToggle');
        const searchInput = this.el.querySelector('.search-overlay input.search-query, #searchInput') || document.querySelector('.search-overlay input.search-query, #searchInput');
        searchOverlay?.classList.add('active');
        searchToggle?.setAttribute('aria-expanded', 'true');
        setTimeout(() => searchInput?.focus(), 300);
    },

    _closeSearch() {
        const searchOverlay = this.el.querySelector('#searchOverlay') || document.querySelector('#searchOverlay');
        const searchToggle = this.el.querySelector('#searchToggle') || document.querySelector('#searchToggle');
        searchOverlay?.classList.remove('active');
        searchToggle?.setAttribute('aria-expanded', 'false');
    },

    _onSearchToggle(e) {
        if (this.editableMode) return;
        e.preventDefault();
        this._openSearch();
    },

    _onSearchClose(e) {
        if (this.editableMode) return;
        e.preventDefault();
        this._closeSearch();
    },

    _onSearchOverlayClick(e) {
        if (this.editableMode) return;
        const searchOverlay = this.el.querySelector('#searchOverlay') || document.querySelector('#searchOverlay');
        if (e.target === searchOverlay) this._closeSearch();
    },

    _initGlobalKeydown() {
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this._closeSearch();
                this._closeMobileMenu();
                this._closeCart();
            }
        });
    },

    /* ============ CART DRAWER ============ */

    _updateCartBadges(quantity) {
        const root = this.el || document;
        const elements = root.querySelectorAll('.js-cart-count, .my_cart_quantity');
        elements.forEach((el) => {
            el.textContent = String(quantity || 0);
            if (quantity) {
                el.classList.remove('d-none');
            }
        });
    },

    _bindCouponFormEvents() {
        const cartTotalEl = this.el.querySelector('#cartTotalWrap') || document.querySelector('#cartTotalWrap');
        if (!cartTotalEl) return;
        cartTotalEl.querySelectorAll('.a-submit').forEach((link) => {
            link.addEventListener('click', (e) => {
                if (this.editableMode) return;
                e.preventDefault();
                link.closest('form')?.submit();
            });
        });
    },

    _renderCartLines(lines, currencySymbol) {
        const cartItemsEl = this.el.querySelector('#cartItems') || document.querySelector('#cartItems');
        if (!cartItemsEl) return;

        if (!lines.length) {
            cartItemsEl.innerHTML = '<p class="empty-state">Your bag is empty. Discover a scent worth carrying.</p>';
            return;
        }

        cartItemsEl.innerHTML = lines
            .map(
                (line) => `
            <div class="cart-item">
                <img src="${line.image_url}" alt="${this.escapeHtml(line.name)}" loading="lazy">
                <div class="cart-item-info">
                    <h4>${this.escapeHtml(line.name)}</h4>
                    <span>${currencySymbol}${line.price.toFixed(2)} &times; ${line.qty}</span>
                </div>
                <div class="cart-item-controls">
                    <button class="qty-decrease" aria-label="Decrease quantity" data-product-id="${line.product_id}" data-line-id="${line.line_id}" data-qty="${line.qty}">&minus;</button>
                    <span>${line.qty}</span>
                    <button class="qty-increase" aria-label="Increase quantity" data-product-id="${line.product_id}" data-line-id="${line.line_id}" data-qty="${line.qty}">+</button>
                    <button class="cart-item-remove" aria-label="Remove item" data-product-id="${line.product_id}" data-line-id="${line.line_id}"><i class="fa-solid fa-trash"></i></button>
                </div>
            </div>`
            )
            .join('');

        cartItemsEl.querySelectorAll('.qty-decrease').forEach((btn) =>
            btn.addEventListener('click', () => {
                if (this.editableMode) return;
                this._changeCartLine(btn.dataset.productId, btn.dataset.lineId, Math.max(parseInt(btn.dataset.qty, 10) - 1, 0));
            })
        );
        cartItemsEl.querySelectorAll('.qty-increase').forEach((btn) =>
            btn.addEventListener('click', () => {
                if (this.editableMode) return;
                this._changeCartLine(btn.dataset.productId, btn.dataset.lineId, parseInt(btn.dataset.qty, 10) + 1);
            })
        );
        cartItemsEl.querySelectorAll('.cart-item-remove').forEach((btn) =>
            btn.addEventListener('click', () => {
                if (this.editableMode) return;
                this._changeCartLine(btn.dataset.productId, btn.dataset.lineId, 0);
            })
        );
    },

    _applyCartData(data) {
        if (!data) return;
        const cartTotalEl = this.el.querySelector('#cartTotalWrap') || document.querySelector('#cartTotalWrap');
        if (Array.isArray(data.lines)) {
            this._renderCartLines(data.lines, data.currency_symbol || '$');
        }
        if (cartTotalEl && data['website_sale.total'] !== undefined) {
            cartTotalEl.innerHTML = data['website_sale.total'];
            this._bindCouponFormEvents();
        }
        this._updateCartBadges(data.cart_quantity);
    },

    async _changeCartLine(productId, lineId, qty) {
        try {
            await this.jsonRpc('/shop/cart/update_json', {
                product_id: parseInt(productId, 10),
                line_id: lineId ? parseInt(lineId, 10) : false,
                set_qty: qty,
                display: true,
            });
            await this._loadCartDrawer();
        } catch (err) {
            this.showToast('Could not update your bag. Please try again.');
        }
    },

    async _loadCartDrawer() {
        const cartItemsEl = this.el.querySelector('#cartItems') || document.querySelector('#cartItems');
        if (!cartItemsEl) return;
        try {
            const data = await this.jsonRpc('/theme_velora/cart_drawer');
            this._applyCartData(data);
        } catch (err) {
            cartItemsEl.innerHTML = '<p class="empty-state">Your bag is empty. Discover a scent worth carrying.</p>';
        }
    },

    _openCart() {
        const cartDrawer = this.el.querySelector('#cartDrawer') || document.querySelector('#cartDrawer');
        const drawerBackdrop = this.el.querySelector('#drawerBackdrop') || document.querySelector('#drawerBackdrop');
        cartDrawer?.classList.add('active');
        drawerBackdrop?.classList.add('active');
        cartDrawer?.setAttribute('aria-hidden', 'false');
        this._loadCartDrawer();
    },

    _closeCart() {
        const cartDrawer = this.el.querySelector('#cartDrawer') || document.querySelector('#cartDrawer');
        const drawerBackdrop = this.el.querySelector('#drawerBackdrop') || document.querySelector('#drawerBackdrop');
        cartDrawer?.classList.remove('active');
        drawerBackdrop?.classList.remove('active');
        cartDrawer?.setAttribute('aria-hidden', 'true');
    },

    _onCartToggle(e) {
        if (this.editableMode) return;
        e.preventDefault();
        this._openCart();
    },

    _onCartToggleMobile(e) {
        if (this.editableMode) return;
        e.preventDefault();
        this._closeMobileMenu();
        this._openCart();
    },

    _onCartClose(e) {
        if (this.editableMode) return;
        e.preventDefault();
        this._closeCart();
    },

    /* ============ CATEGORY QUICK-FILTER ============ */

    _onCategoryCardClick(e) {
        if (this.editableMode) return;
        const card = e.currentTarget;
        const note = card.dataset.note;
        if (note) {
            this.showToast(`Exploring ${note} fragrances`);
        }
        const bestsellers = this.el.querySelector('#velora_bestsellers') || document.querySelector('#velora_bestsellers');
        bestsellers?.scrollIntoView({ behavior: 'smooth' });
    },

    /* ============ WISHLIST HELPERS & EVENTS ============ */

    _getWishlistIds() {
        try {
            return JSON.parse(sessionStorage.getItem('website_sale_wishlist_product_ids') || '[]');
        } catch {
            return [];
        }
    },

    _setWishlistIds(ids) {
        sessionStorage.setItem('website_sale_wishlist_product_ids', JSON.stringify(ids));
    },

    _updateWishCountBadge(count) {
        const n = typeof count === 'number' ? count : count.length;
        const badges = this.el.querySelectorAll('.js-wishlist-count, .my_wish_quantity');
        badges.forEach((el) => (el.textContent = String(n)));

        const hideEls = this.el.querySelectorAll('.o_wsale_my_wish_hide_empty');
        hideEls.forEach((el) => el.classList.toggle('d-none', n === 0));
    },

    _markWishlistBtn(btn, inWish) {
        const icon = btn.querySelector('i');
        if (inWish) {
            btn.classList.add('vc-in-wish', 'active');
            btn.setAttribute('disabled', 'disabled');
            if (icon) {
                icon.classList.remove('fa-regular');
                icon.classList.add('fa-solid');
            }
        } else {
            btn.classList.remove('vc-in-wish', 'active');
            btn.removeAttribute('disabled');
            if (icon) {
                icon.classList.add('fa-regular');
                icon.classList.remove('fa-solid');
            }
        }
    },

    _initWishlistBtns() {
        const ids = this._getWishlistIds();
        const btns = this.el.querySelectorAll('.wishlist-btn[data-product-product-id]');

        // Sync: collect all product IDs that the server already marked as wishlisted
        // (button rendered with 'vc-in-wish active' class by QWeb) and seed sessionStorage
        const serverWishIds = [...ids];
        btns.forEach((btn) => {
            const pid = parseInt(btn.dataset.productProductId, 10);
            if (btn.classList.contains('vc-in-wish') && pid && !serverWishIds.includes(pid)) {
                serverWishIds.push(pid);
            }
        });
        if (serverWishIds.length !== ids.length) {
            this._setWishlistIds(serverWishIds);
        }

        btns.forEach((btn) => {
            const pid = parseInt(btn.dataset.productProductId, 10);
            if (serverWishIds.includes(pid)) this._markWishlistBtn(btn, true);
        });

        const qtyEl = this.el.querySelector('.my_wish_quantity') || document.querySelector('.my_wish_quantity');
        const serverCount = parseInt(qtyEl?.textContent?.trim() || '0', 10);
        if (!isNaN(serverCount)) this._updateWishCountBadge(serverCount);
    },

    async _onWishlistBtnClick(e) {
        if (this.editableMode) return;
        const btn = e.currentTarget;
        if (btn.hasAttribute('disabled')) return;

        e.preventDefault();
        e.stopPropagation();

        const productId = parseInt(btn.dataset.productProductId, 10);
        if (!productId) return;

        const ids = this._getWishlistIds();
        // Already tracked locally — button is already marked, nothing to do
        if (ids.includes(productId)) {
            this.showToast('Already in your wishlist \u2665');
            return;
        }

        // Optimistically update UI
        this._markWishlistBtn(btn, true);
        const newIds = [...ids, productId];
        this._setWishlistIds(newIds);
        this._updateWishCountBadge(newIds.length);

        try {
            await this.jsonRpc('/shop/wishlist/add', { product_id: productId });
            this.showToast('Added to wishlist \u2665');
        } catch (err) {
            // Odoo raises a UserError for duplicate wishlist entries (DB unique constraint).
            // Treat this as "already wishlisted" — keep the button active & show a friendly message.
            const msg = (err && err.message) ? err.message.toLowerCase() : '';
            const isDuplicate = msg.includes('duplicate') || msg.includes('unique') || msg.includes('already');
            if (isDuplicate) {
                // Product is already on the server wishlist — keep button active
                this.showToast('Already in your wishlist \u2665');
            } else {
                // Genuine error — roll back the optimistic UI update
                this._markWishlistBtn(btn, false);
                const rolled = ids.filter((id) => id !== productId);
                this._setWishlistIds(rolled);
                this._updateWishCountBadge(rolled.length);
                this.showToast('Could not add to wishlist. Please try again.');
            }
        }
    },

    _onOdooWishlistBtnClick(e) {
        if (this.editableMode) return;
        const btn = e.currentTarget;
        if (btn && !btn.disabled) {
            this.showToast('Added to wishlist ✓');
        }
    },

    /* ============ SCROLL REVEAL (INTERSECTION OBSERVER) ============ */

    _initScrollReveal() {
        const revealItems = this.el.querySelectorAll('.reveal');
        if (!revealItems.length) return;

        const revealObserver = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('in-view');
                        revealObserver.unobserve(entry.target);
                    }
                });
            },
            { threshold: 0.15, rootMargin: '0px 0px -50px 0px' }
        );
        revealItems.forEach((item) => revealObserver.observe(item));
    },

    /* ============ COUNT-UP STATISTICS ============ */

    _initCountUpStats() {
        const statNumbers = this.el.querySelectorAll('.stat-number');
        if (!statNumbers.length) return;

        const statObserver = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        if (!this.editableMode) {
                            this._animateCount(entry.target);
                        }
                        statObserver.unobserve(entry.target);
                    }
                });
            },
            { threshold: 0.5 }
        );
        statNumbers.forEach((el) => statObserver.observe(el));
    },

    _animateCount(el) {
        const rawTextNum = parseInt(el.textContent.replace(/[^\d]/g, ''), 10);
        let target = parseInt(el.dataset.count, 10);
        if (!isNaN(rawTextNum) && rawTextNum > 0 && rawTextNum !== target) {
            target = rawTextNum;
            el.dataset.count = target;
        }
        if (isNaN(target)) return;

        const duration = 1800;
        const startTime = performance.now();

        const tick = (now) => {
            const progress = Math.min((now - startTime) / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3);
            const value = Math.floor(eased * target);
            el.textContent = value.toLocaleString();
            if (progress < 1) {
                requestAnimationFrame(tick);
            } else {
                el.textContent = target.toLocaleString();
            }
        };
        requestAnimationFrame(tick);
    },

    /* ============ DYNAMIC FEATURED COLLECTIONS ============ */

    _onCollectionCardClick(e) {
        if (this.editableMode) return;
        if (e.target.closest('a') || e.target.closest('button')) return;
        const card = e.currentTarget;
        const titleEl = card.querySelector('h3, .h3');
        if (!titleEl) return;
        const categoryName = titleEl.textContent.trim();
        if (categoryName) {
            e.preventDefault();
            e.stopPropagation();
            window.location.href = `/collections/redirect?name=${encodeURIComponent(categoryName)}`;
        }
    },

    _onCollectionsLinkClick(e) {
        if (this.editableMode) return;
        const link = e.currentTarget;
        const href = link.getAttribute('href');
        if (href && href.startsWith('/collections/')) {
            const card = link.closest('.collection-card, .collection-overlay, .collections-page-card');
            if (card) {
                const h3 = card.querySelector('h3');
                if (h3) {
                    const categoryName = h3.textContent.trim();
                    if (categoryName) {
                        e.preventDefault();
                        window.location.href = `/collections/redirect?name=${encodeURIComponent(categoryName)}`;
                    }
                }
            }
        }
    },

    /* ============ TESTIMONIAL CAROUSEL ============ */

    _initTestimonialCarousel() {
        const testimonialTrack = this.el.querySelector('#testimonialTrack') || document.querySelector('#testimonialTrack');
        const testimonialDots = this.el.querySelector('#testimonialDots') || document.querySelector('#testimonialDots');
        const testimonialWrap = this.el.querySelector('.testimonial-track-wrap') || document.querySelector('.testimonial-track-wrap');

        if (!testimonialTrack || !testimonialDots) return;

        const cards = Array.from(testimonialTrack.querySelectorAll('.testimonial-card'));
        let activeIndex = 0;

        const goToTestimonial = (index) => {
            if (this.editableMode) return;
            const target = (index + cards.length) % cards.length;
            const card = cards[target];
            const trackRect = testimonialTrack.getBoundingClientRect();
            const cardRect = card.getBoundingClientRect();
            const scrollLeft = testimonialTrack.scrollLeft + (cardRect.left - trackRect.left);
            testimonialTrack.scrollTo({ left: scrollLeft, behavior: 'smooth' });
        };

        cards.forEach((_, i) => {
            const dot = document.createElement('button');
            dot.setAttribute('aria-label', `Go to testimonial ${i + 1}`);
            if (i === 0) dot.classList.add('active');
            dot.addEventListener('click', () => {
                if (this.editableMode) return;
                goToTestimonial(i);
            });
            testimonialDots.appendChild(dot);
        });

        const dotEls = Array.from(testimonialDots.querySelectorAll('button'));
        const dotObserver = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                const index = cards.indexOf(entry.target);
                if (entry.isIntersecting && index > -1) {
                    activeIndex = index;
                    dotEls.forEach((d) => d.classList.remove('active'));
                    dotEls[index]?.classList.add('active');
                }
            });
        }, { root: testimonialTrack, threshold: 0.6 });
        cards.forEach((card) => dotObserver.observe(card));

        const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        const AUTOPLAY_DELAY = 5000;

        const startAutoplay = () => {
            if (this.editableMode || prefersReducedMotion) return;
            stopAutoplay();
            this.autoplayTimer = setInterval(() => goToTestimonial(activeIndex + 1), AUTOPLAY_DELAY);
        };
        const stopAutoplay = () => {
            clearInterval(this.autoplayTimer);
        };

        const targetWrap = testimonialWrap || testimonialTrack;
        targetWrap.addEventListener('mouseenter', stopAutoplay);
        targetWrap.addEventListener('mouseleave', startAutoplay);
        testimonialTrack.addEventListener('focusin', stopAutoplay);
        testimonialTrack.addEventListener('focusout', startAutoplay);
        testimonialTrack.addEventListener('touchstart', stopAutoplay, { passive: true });
        testimonialTrack.addEventListener('touchend', startAutoplay, { passive: true });
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) stopAutoplay();
            else startAutoplay();
        });

        const sectionVisibilityObserver = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) startAutoplay();
                    else stopAutoplay();
                });
            },
            { threshold: 0.4 }
        );
        sectionVisibilityObserver.observe(targetWrap);

        const updateEdgeFades = () => {
            if (!testimonialWrap) return;
            const maxScroll = testimonialTrack.scrollWidth - testimonialTrack.clientWidth;
            testimonialWrap.classList.toggle('show-left-fade', testimonialTrack.scrollLeft > 8);
            testimonialWrap.classList.toggle('show-right-fade', testimonialTrack.scrollLeft < maxScroll - 8);
        };
        testimonialTrack.addEventListener('scroll', updateEdgeFades, { passive: true });
        window.addEventListener('resize', updateEdgeFades);
        updateEdgeFades();
    },

    /* ============ FAQ ACCORDION ============ */

    _onAccordionHeaderClick(e) {
        if (this.editableMode) return;
        const header = e.currentTarget;
        const isOpen = header.getAttribute('aria-expanded') === 'true';

        const allHeaders = this.el.querySelectorAll('.accordion-header');
        allHeaders.forEach((h) => h.setAttribute('aria-expanded', 'false'));

        if (!isOpen) {
            header.setAttribute('aria-expanded', 'true');
        }
    },

    /* ============ NEWSLETTER FORM ============ */

    _onNewsletterSubmit(e) {
        if (this.editableMode) return;
        e.preventDefault();
        const form = e.currentTarget;
        const formMessage = form.querySelector('#formMessage') || this.el.querySelector('#formMessage');
        const emailInput = form.querySelector('#newsletterEmail') || this.el.querySelector('#newsletterEmail');
        const email = emailInput?.value?.trim() || '';
        const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

        if (!emailPattern.test(email)) {
            if (formMessage) {
                formMessage.textContent = 'Please enter a valid email address.';
                formMessage.style.color = '#e07a7a';
            }
            return;
        }

        if (formMessage) {
            formMessage.textContent = `Thank you! ${email} has joined the Velora Circle.`;
            formMessage.style.color = '';
        }
        form.reset();
        this.showToast('Subscribed successfully');
    },

    /* ============ SEARCH RESULTS HEADER ============ */

    _initSearchResultsHeader() {
        const isSearchPage = window.location.pathname.startsWith('/website/search') ||
            document.querySelector('.velora-search-results-page') !== null ||
            document.querySelector('.o_search_result_item') !== null;
        if (isSearchPage) {
            const siteHeader = this.el.querySelector('#siteHeader') || document.querySelector('#siteHeader');
            if (siteHeader) {
                siteHeader.classList.add('header-black');
            }
            const wrap = this.el.querySelector('#wrap') || document.querySelector('#wrap');
            if (wrap && !wrap.classList.contains('velora-search-results-page')) {
                wrap.classList.add('velora-search-results-page');
            }
            document.body?.classList.add('velora-search-page');
        }
    },

    /* ============ CONTACT FORM VALIDATION ============ */

    _showFieldError(input, message) {
        if (!input) return;
        input.classList.add('is-invalid');
        const formField = input.closest('.form-field') || input.closest('.s_website_form_field') || input.parentElement;
        if (formField) {
            formField.classList.add('o_has_error');
            let errorEl = formField.querySelector('.velora-field-error');
            if (!errorEl) {
                errorEl = document.createElement('div');
                errorEl.className = 'velora-field-error';
                errorEl.setAttribute('role', 'alert');
                formField.appendChild(errorEl);
            }
            errorEl.textContent = message;
        }
    },

    _clearFieldError(input) {
        if (!input) return;
        input.classList.remove('is-invalid');
        const formField = input.closest('.form-field') || input.closest('.s_website_form_field') || input.parentElement;
        if (formField) {
            formField.classList.remove('o_has_error');
            const errorEl = formField.querySelector('.velora-field-error');
            if (errorEl) {
                errorEl.remove();
            }
        }
    },

    _validateEmail(value) {
        if (!value) {
            return { valid: false, message: 'Email address is required.' };
        }
        if (/\s/.test(value)) {
            return { valid: false, message: 'Email address cannot contain spaces.' };
        }
        if (!value.includes('@')) {
            return { valid: false, message: "Please include an '@' in the email address." };
        }
        const parts = value.split('@');
        if (parts.length !== 2) {
            return { valid: false, message: "Email address must contain exactly one '@'." };
        }
        const [localPart, domainPart] = parts;
        if (!localPart) {
            return { valid: false, message: "Please enter the username before '@'." };
        }
        if (!domainPart) {
            return { valid: false, message: "Please enter a domain after '@'." };
        }
        if (!domainPart.includes('.')) {
            return { valid: false, message: "Domain name must include a dot and extension (e.g. .com)." };
        }
        if (domainPart.startsWith('.') || domainPart.endsWith('.')) {
            return { valid: false, message: "Domain name cannot start or end with a dot." };
        }
        const domainParts = domainPart.split('.');
        const tld = domainParts[domainParts.length - 1];
        if (!tld || tld.length < 2) {
            return { valid: false, message: "Please enter a valid top-level domain (e.g. .com, .org)." };
        }
        const strictEmailRegex = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+$/;
        if (!strictEmailRegex.test(value)) {
            return { valid: false, message: 'Please enter a valid email address (e.g. name@example.com).' };
        }
        return { valid: true, message: '' };
    },

    _validateContactField(input) {
        if (!input) return true;
        const name = input.getAttribute('name');
        const value = (input.value || '').trim();

        if (name === 'email_from' || name === 'email' || input.type === 'email') {
            const res = this._validateEmail(value);
            if (!res.valid) {
                this._showFieldError(input, res.message);
                return false;
            }
            this._clearFieldError(input);
            return true;
        }

        if (name === 'name' || input.id === 'vc_name' || input.id === 'contactName') {
            if (!value) {
                this._showFieldError(input, 'Full name is required.');
                return false;
            }
            if (value.length < 2) {
                this._showFieldError(input, 'Name must be at least 2 characters.');
                return false;
            }
            this._clearFieldError(input);
            return true;
        }

        if (name === 'subject' || input.id === 'vc_subject' || input.id === 'contactSubject') {
            if (!value) {
                this._showFieldError(input, 'Subject is required.');
                return false;
            }
            this._clearFieldError(input);
            return true;
        }

        if (name === 'description' || name === 'message' || input.tagName?.toLowerCase() === 'textarea' || input.id === 'vc_message' || input.id === 'contactMessage') {
            if (!value) {
                this._showFieldError(input, 'Message is required.');
                return false;
            }
            if (value.length < 5) {
                this._showFieldError(input, 'Message must be at least 5 characters.');
                return false;
            }
            this._clearFieldError(input);
            return true;
        }

        this._clearFieldError(input);
        return true;
    },

    _validateContactForm(form) {
        if (!form) return true;
        const inputs = Array.from(form.querySelectorAll(
            'input[name="name"], input[name="email_from"], input[name="email"], input[name="subject"], textarea[name="description"], textarea[name="message"], #vc_name, #vc_email, #vc_subject, #vc_message, #contactName, #contactEmail, #contactSubject, #contactMessage'
        )).filter((input, idx, arr) => arr.indexOf(input) === idx);

        let isValid = true;
        let firstInvalid = null;

        for (const input of inputs) {
            const ok = this._validateContactField(input);
            if (!ok) {
                isValid = false;
                if (!firstInvalid) {
                    firstInvalid = input;
                }
            }
        }

        if (!isValid && firstInvalid) {
            firstInvalid.focus();
            try {
                firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
            } catch (_) {}
            this.showToast('Please correct the highlighted fields before sending.');
        }

        return isValid;
    },

    _initContactFormValidation() {
        const forms = (this.el || document).querySelectorAll('#contactus_form, #contactForm, .contact-form form');
        if (!forms.length) return;

        forms.forEach((form) => {
            const inputs = Array.from(form.querySelectorAll(
                'input[name="name"], input[name="email_from"], input[name="email"], input[name="subject"], textarea[name="description"], textarea[name="message"], #vc_name, #vc_email, #vc_subject, #vc_message, #contactName, #contactEmail, #contactSubject, #contactMessage'
            )).filter((input, idx, arr) => arr.indexOf(input) === idx);

            inputs.forEach((input) => {
                input.addEventListener('input', () => {
                    if (input.classList.contains('is-invalid')) {
                        this._validateContactField(input);
                    }
                });

                input.addEventListener('blur', () => {
                    if ((input.value || '').trim().length > 0 || input.classList.contains('is-invalid')) {
                        this._validateContactField(input);
                    }
                });
            });

            const handleSubmitAttempt = (e) => {
                if (this.editableMode) return;
                const valid = this._validateContactForm(form);
                if (!valid) {
                    e.preventDefault();
                    e.stopPropagation();
                    if (typeof e.stopImmediatePropagation === 'function') {
                        e.stopImmediatePropagation();
                    }
                    return false;
                }
            };

            const sendBtns = form.querySelectorAll('.s_website_form_send, [type="submit"]');
            sendBtns.forEach((btn) => {
                btn.addEventListener('click', handleSubmitAttempt, true);
            });
            form.addEventListener('submit', handleSubmitAttempt, true);
        });
    },

    _onContactSubmit(e) {
        if (this.editableMode) return;
        const form = e.currentTarget;
        const valid = this._validateContactForm(form);
        if (!valid) {
            e.preventDefault();
            e.stopPropagation();
            if (typeof e.stopImmediatePropagation === 'function') {
                e.stopImmediatePropagation();
            }
            return;
        }

        // If it's a simple custom form (not standard s_website_form)
        if (!form.classList.contains('o_mark_required') && form.getAttribute('action') !== '/website/form/') {
            e.preventDefault();
            const contactFormMessage = form.querySelector('#contactFormMessage') || this.el.querySelector('#contactFormMessage');
            const name = form.querySelector('#contactName, input[name="name"]')?.value?.trim() || '';
            const email = form.querySelector('#contactEmail, input[name="email_from"]')?.value?.trim() || '';

            if (contactFormMessage) {
                contactFormMessage.textContent = `Thank you, ${name}. Our concierge team will reply to ${email} shortly.`;
                contactFormMessage.style.color = '';
            }
            form.reset();
            this.showToast('Message sent successfully');
        }
    },

    /* ============ AJAX ADD TO CART ============ */

    async _onCartFormSubmit(e) {
        if (this.editableMode) return;
        const form = e.currentTarget;
        const btn = form.querySelector('.add-cart-btn, .shop-add-cart-btn, button[type="submit"]');

        e.preventDefault();

        let productId = parseInt(form.querySelector('[name="product_id"]')?.value, 10);
        if (!productId && form.dataset.productId) {
            productId = parseInt(form.dataset.productId, 10);
        }
        const addQty = parseFloat(form.querySelector('[name="add_qty"]')?.value || '1');
        if (!productId) return;

        if (btn) btn.disabled = true;
        const originalHtml = btn ? btn.innerHTML : '';
        if (btn) btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';

        try {
            const data = await this.jsonRpc('/shop/cart/update_json', {
                product_id: productId,
                add_qty: addQty,
                display: true,
            });
            this._applyCartData(data);
            this.showToast('Added to your bag ✓');
            this._openCart();
        } catch (err) {
            this.showToast('Could not add to bag. Please try again.');
        } finally {
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = originalHtml;
            }
        }
    },

    async _onAddCartBtnClick(e) {
        if (this.editableMode) return;
        const btn = e.currentTarget;
        if (btn.closest('form')) return;

        e.preventDefault();
        if (btn.disabled) return;

        const productId = parseInt(btn.dataset.productId, 10);
        if (!productId) return;

        btn.disabled = true;
        const originalHtml = btn.innerHTML;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';

        try {
            const data = await this.jsonRpc('/shop/cart/update_json', {
                product_id: productId,
                add_qty: 1,
                display: true,
            });
            this._applyCartData(data);
            this.showToast('Added to your bag ✓');
            this._openCart();
        } catch (err) {
            this.showToast('Could not add to bag. Please try again.');
        } finally {
            btn.disabled = false;
            btn.innerHTML = originalHtml;
        }
    },

    /* ============ FOOTER YEAR ============ */

    _initFooterYear() {
        const yearEl = this.el.querySelector('#year') || document.querySelector('#year');
        if (yearEl) yearEl.textContent = new Date().getFullYear();
    },

    /* ============ WISHLIST PAGE ADD TO CART ============ */

    async _onWishlistPageAddCartClick(e) {
        if (this.editableMode) return;
        const btn = e.currentTarget;
        if (btn.classList.contains('disabled')) return;

        e.preventDefault();
        e.stopPropagation();
        e.stopImmediatePropagation();

        const tr = btn.closest('tr');
        if (!tr) return;

        const productId = parseInt(tr.dataset.productId, 10);
        const wishId = parseInt(tr.dataset.wishId, 10);
        if (!productId) return;

        btn.disabled = true;
        btn.classList.add('disabled');
        const originalHtml = btn.innerHTML;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';

        try {
            const data = await this.jsonRpc('/shop/cart/update_json', {
                product_id: productId,
                add_qty: 1,
                display: true,
            });
            if (data && data.cart_quantity !== undefined) {
                this._updateCartBadges(data.cart_quantity);
            }

            const b2bWish = document.getElementById('b2b_wish');
            const keepInWishlist = b2bWish && b2bWish.checked;

            if (!keepInWishlist && wishId) {
                await this.jsonRpc(`/shop/wishlist/remove/${wishId}`);
                let sessionIds = this._getWishlistIds().filter((id) => id !== productId);
                this._setWishlistIds(sessionIds);
                this._updateWishCountBadge(sessionIds.length);

                tr.classList.add('velora-row-removing');
                setTimeout(() => {
                    tr.remove();
                    const remainingRows = document.querySelectorAll('.velora-wishlist-page #o_comparelist_table tbody tr');
                    if (remainingRows.length === 0) {
                        window.location.href = '/shop/cart';
                    }
                }, 400);
            }

            await this._loadCartDrawer();
            this.showToast('Added to your bag ✓');
            this._openCart();
        } catch (err) {
            this.showToast('Could not add to bag. Please try again.');
        } finally {
            btn.disabled = false;
            btn.classList.remove('disabled');
            btn.innerHTML = originalHtml;
        }
    },

    /* ============ USER MENU DROPDOWN ============ */

    _onUserMenuButtonClick(e) {
        if (this.editableMode) return;
        const userMenuButton = e.currentTarget;
        const userDropdown = this.el.querySelector('.velora-user-dropdown') || document.querySelector('.velora-user-dropdown');

        if (userMenuButton && userDropdown) {
            e.preventDefault();
            e.stopPropagation();
            const isExpanded = userMenuButton.getAttribute('aria-expanded') === 'true';
            userMenuButton.setAttribute('aria-expanded', String(!isExpanded));
            userDropdown.classList.toggle('show');
        }
    },

    _initUserDropdownDismiss() {
        document.addEventListener('click', (e) => {
            if (this.editableMode) return;
            const userDropdown = this.el.querySelector('.velora-user-dropdown') || document.querySelector('.velora-user-dropdown');
            if (userDropdown && userDropdown.classList.contains('show')) {
                if (!e.target.closest('.user-dropdown-wrap')) {
                    const button = this.el.querySelector('#userMenuButton') || document.querySelector('#userMenuButton');
                    if (button) button.setAttribute('aria-expanded', 'false');
                    userDropdown.classList.remove('show');
                }
            }
        });
    },
});

export default publicWidget.registry.ThemeVelora;
