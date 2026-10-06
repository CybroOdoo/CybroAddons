/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Interaction } from "@web/public/interaction";
import { rpc } from "@web/core/network/rpc";
import wishlistUtils from "@website_sale_wishlist/js/website_sale_wishlist_utils";

export class ThemeVeloraInteraction extends Interaction {
    static selector = "#cartDrawer";

    setup() {
        this.toastTimer = null;
        
        this.onScroll = this.onScroll.bind(this);
        this.onGlobalKeydown = this.onGlobalKeydown.bind(this);
        this.onDocumentClick = this.onDocumentClick.bind(this);
        this.onDocumentSubmit = this.onDocumentSubmit.bind(this);
        this.onDocumentInput = this.onDocumentInput.bind(this);
        this.onDocumentFocusOut = this.onDocumentFocusOut.bind(this);
        this.updateEdgeFades = this.updateEdgeFades.bind(this);
        this.syncWishlistButtons = this.syncWishlistButtons.bind(this);
        this.searchDebounceTimer = null;
    }

    start() {
        if (document.body.classList.contains('editor_enable')) {
            return; // Avoid interfering with Website Builder
        }

        this.addListener(this.el, 'scroll', this.onScroll, { passive: true, capture: true });
        this.addListener(document, 'scroll', this.onScroll, { passive: true, capture: true });
        this.addListener(document, 'keydown', this.onGlobalKeydown);
        this.addListener(document, 'click', this.onDocumentClick);
        this.addListener(document, 'submit', this.onDocumentSubmit);
        this.addListener(document, 'input', this.onDocumentInput);
        this.addListener(document, 'focusout', this.onDocumentFocusOut);

        this.onScroll();
        this.fetchCartData();
        this.initObservers();
        this.initTestimonials();
        this.syncWishlistButtons();
        
        if (window.location.pathname.includes('thank-you') || document.querySelector('.fa-paper-plane')) {
            document.body.classList.add('is-contact-success-page');
        }
        
        const yearEl = document.querySelector('#year');
        if (yearEl) yearEl.textContent = new Date().getFullYear();
    }

    // Utilities
    $(sel) { return document.querySelector(sel); }
    $$(sel) { return Array.from(document.querySelectorAll(sel)); }
    
    formatCurrency(amount, symbol, position) {
        const formatted = parseFloat(amount).toFixed(2);
        return position === 'after' ? `${formatted} ${symbol}` : `${symbol}${formatted}`;
    }

    showToast(message) {
        const toast = document.querySelector('#toast');
        if (!toast) return;
        toast.textContent = message;
        toast.classList.add('show');
        clearTimeout(this.toastTimer);
        this.toastTimer = setTimeout(() => toast.classList.remove('show'), 2600);
    }

    syncWishlistButtons() {
        if (!wishlistUtils) return;
        const wishlistIds = wishlistUtils.getWishlistProductIds();
        this.$$('.wishlist-btn, .o_add_wishlist').forEach(btn => {
            const form = btn.closest('form');
            const productId = parseInt(
                btn.dataset.productProductId ||
                btn.dataset.productId ||
                form?.querySelector('input[name="product_id"]')?.value
            );
            const inWish = productId && wishlistIds.includes(productId);
            btn.classList.toggle('active', !!inWish);
            const icon = btn.querySelector('i');
            if (icon) {
                if (inWish) {
                    icon.classList.remove('fa-regular');
                    icon.classList.add('fa-solid');
                } else {
                    icon.classList.remove('fa-solid');
                    icon.classList.add('fa-regular');
                }
            }
            btn.setAttribute('aria-pressed', String(!!inWish));
        });
    }

    async addToWishlist(wishlistBtn, productId) {
        const wishlistIds = wishlistUtils ? wishlistUtils.getWishlistProductIds() : [];
        if (wishlistBtn.classList.contains('active') || wishlistIds.includes(productId)) {
            this.showToast('Already in wishlist!');
            wishlistBtn.classList.add('active');
            const icon = wishlistBtn.querySelector('i');
            if (icon) {
                icon.classList.remove('fa-regular');
                icon.classList.add('fa-solid');
            }
            wishlistBtn.setAttribute('aria-pressed', 'true');
            return;
        }

        try {
            await rpc('/shop/wishlist/add', { product_id: productId });
            if (wishlistUtils) {
                wishlistUtils.addWishlistProduct(productId);
                wishlistUtils.updateWishlistNavBar();
            }
            this.syncWishlistButtons();
            this.showToast('Added to wishlist');
        } catch (error) {
            const currentWishIds = wishlistUtils ? wishlistUtils.getWishlistProductIds() : [];
            if (currentWishIds.includes(productId)) {
                this.showToast('Already in wishlist!');
                this.syncWishlistButtons();
            } else {
                this.showToast('Could not add to wishlist');
            }
        }
    }

    jsonRpc(url, params) {
        return fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ jsonrpc: '2.0', method: 'call', id: Date.now(), params: params || {} }),
        })
        .then(res => res.json())
        .then(data => {
            if (data.error) throw new Error(data.error.message || 'RPC Error');
            return data.result;
        });
    }

    // Event Handlers
    onScroll() {
        const wrapwrap = this.el;
        const scrollTop = wrapwrap.scrollTop || window.scrollY || document.documentElement.scrollTop || 0;
        const docHeight = wrapwrap.scrollHeight > wrapwrap.clientHeight 
            ? wrapwrap.scrollHeight - wrapwrap.clientHeight 
            : document.documentElement.scrollHeight - window.innerHeight;
          
        const progress = docHeight > 0 ? (scrollTop / docHeight) * 100 : 0;
        const scrollProgress = document.querySelector('#scrollProgress');
        if (scrollProgress) scrollProgress.style.width = `${progress}%`;

        const currentHeader = document.querySelector('.site-header');
        if (scrollTop > 60) {
            currentHeader?.classList.add('scrolled');
        } else {
            currentHeader?.classList.remove('scrolled');
        }

        const backToTop = document.querySelector('#backToTop');
        if (scrollTop > 500) {
            backToTop?.classList.add('show');
        } else {
            backToTop?.classList.remove('show');
        }
    }

    onBackToTop() {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    onToggleMobileMenu() {
        const hamburger = this.$('#hamburger');
        const mobileMenu = this.$('#mobileMenu');
        if (!hamburger) return;
        const isActive = hamburger.classList.toggle('active');
        hamburger.setAttribute('aria-expanded', String(isActive));
        mobileMenu?.classList.toggle('active', isActive);
    }

    onCloseMobileMenu() {
        const hamburger = this.$('#hamburger');
        const mobileMenu = this.$('#mobileMenu');
        hamburger?.classList.remove('active');
        hamburger?.setAttribute('aria-expanded', 'false');
        mobileMenu?.classList.remove('active');
    }

    onOpenSearch() {
        const searchOverlay = this.$('#searchOverlay');
        const searchToggle = this.$('#searchToggle');
        const searchInput = this.$('#searchInput');
        searchOverlay?.classList.add('active');
        searchToggle?.setAttribute('aria-expanded', 'true');
        setTimeout(() => {
            searchInput?.focus();
            if (searchInput?.value) searchInput.select();
        }, 150);
    }

    onCloseSearch() {
        const searchOverlay = this.$('#searchOverlay');
        const searchToggle = this.$('#searchToggle');
        const resultsContainer = this.$('#searchResults');
        searchOverlay?.classList.remove('active');
        searchToggle?.setAttribute('aria-expanded', 'false');
        if (resultsContainer) {
            resultsContainer.innerHTML = '';
            resultsContainer.classList.add('d-none');
        }
    }

    onDocumentInput(e) {
        if (e.target.matches('#searchInput')) {
            clearTimeout(this.searchDebounceTimer);
            const query = e.target.value.trim();
            const resultsContainer = this.$('#searchResults');
            if (!resultsContainer) return;

            if (query.length < 2) {
                resultsContainer.innerHTML = '';
                resultsContainer.classList.add('d-none');
                return;
            }

            this.searchDebounceTimer = setTimeout(() => {
                this.fetchSearchResults(query);
            }, 250);
        }

        if (e.target.closest('#contactForm')) {
            const input = e.target;
            if (input.matches('input, textarea')) {
                if (input.classList.contains('is-invalid') || input.closest('.o_has_error')) {
                    this.validateContactField(input);
                }
            }
        }

        const newsletterInput = e.target.closest('.newsletter-form input[type="email"], #newsletterEmail');
        if (newsletterInput && newsletterInput.classList.contains('is-invalid')) {
            if (/^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(newsletterInput.value.trim())) {
                newsletterInput.classList.remove('is-invalid');
                const formMessage = newsletterInput.closest('.newsletter-form, section')?.querySelector('.form-message, #formMessage');
                if (formMessage) formMessage.textContent = '';
            }
        }
    }

    onDocumentFocusOut(e) {
        if (!e.target || !e.target.closest) return;
        if (!e.target.closest('#contactForm')) return;
        const input = e.target;
        if (input.matches('input, textarea')) {
            if (input.value.trim() !== '' || input.classList.contains('is-invalid')) {
                this.validateContactField(input);
            }
        }
    }

    async fetchSearchResults(query) {
        const resultsContainer = this.$('#searchResults');
        if (!resultsContainer) return;

        try {
            const data = await rpc('/website/snippet/autocomplete', {
                search_type: 'products',
                term: query,
                limit: 5,
            });

            if (!this.$('#searchOverlay')?.classList.contains('active')) return;
            const currentInput = this.$('#searchInput')?.value.trim();
            if (currentInput !== query) return;

            if (data && data.results && data.results.length > 0) {
                let html = '<div class="search-results-list">';
                data.results.forEach(item => {
                    const imgUrl = item.image_url || `/web/image/product.template/${item.id}/image_128`;
                    const price = item.detail || '';
                    html += `
                        <a href="${item.website_url || `/shop/${item.id}`}" class="search-result-item">
                            <img src="${imgUrl}" alt="${item.name}" class="search-result-thumb" loading="lazy"/>
                            <div class="search-result-info">
                                <span class="search-result-title">${item.name}</span>
                                ${price ? `<span class="search-result-price">${price}</span>` : ''}
                            </div>
                            <i class="fa-solid fa-arrow-right search-result-arrow"></i>
                        </a>
                    `;
                });
                html += '</div>';
                const totalCount = data.results_count || data.results.length;
                html += `
                    <a href="/shop?search=${encodeURIComponent(query)}" class="search-result-view-all">
                        <span>View all ${totalCount} results</span>
                        <i class="fa-solid fa-arrow-right"></i>
                    </a>
                `;
                resultsContainer.innerHTML = html;
                resultsContainer.classList.remove('d-none');
            } else {
                resultsContainer.innerHTML = `
                    <div class="search-no-results">
                        <p>No fragrances found for "<em>${query}</em>"</p>
                        <a href="/shop" class="search-browse-link">Browse all collections</a>
                    </div>
                `;
                resultsContainer.classList.remove('d-none');
            }
        } catch (error) {
            console.warn('Search autocomplete error:', error);
        }
    }

    onSearchOverlayClick(e) {
        // Handled in onDocumentClick
    }

    onGlobalKeydown(e) {
        if (e.key === 'Escape') {
            this.onCloseSearch();
            this.onCloseMobileMenu();
            this.onCloseCart();
        }
    }

    // Global interception for add to cart, wishlist, and UI toggles
    onDocumentClick(e) {
        const newsletterBtn = e.target.closest('.newsletter-form a.btn, .newsletter-form .newsletter-submit-btn, .newsletter-form button, #newsletterForm a.btn, #newsletterForm button');
        if (newsletterBtn) {
            const form = newsletterBtn.closest('.newsletter-form, #newsletterForm');
            if (form) {
                e.preventDefault();
                e.stopPropagation();
                this.submitNewsletter(form, newsletterBtn);
                return;
            }
        }

        const contactSendBtn = e.target.closest('#contactForm .s_website_form_send');
        if (contactSendBtn) {
            const form = contactSendBtn.closest('form');
            if (form && !this.validateContactForm(form)) {
                e.preventDefault();
                e.stopImmediatePropagation();
                return;
            }
        }

        if (e.target.closest('#backToTop')) this.onBackToTop();
        if (e.target.closest('#hamburger')) this.onToggleMobileMenu();
        if (e.target.closest('#mobileMenuClose') || e.target.closest('.mobile-menu a') || e.target.closest('#wishlistToggleMobile')) this.onCloseMobileMenu();
        if (e.target.closest('#mobileSearchBtn')) {
            this.onCloseMobileMenu();
            this.onOpenSearch();
        }
        if (e.target.closest('#searchToggle')) this.onOpenSearch();
        if (e.target.closest('#searchClose')) this.onCloseSearch();
        if (e.target.closest('#searchOverlay') && e.target === this.$('#searchOverlay')) this.onCloseSearch();
        if (e.target.closest('#cartToggle')) { e.preventDefault(); this.onOpenCart(); }
        if (e.target.closest('#cartClose') || e.target.closest('#drawerBackdrop')) this.onCloseCart();
        if (e.target.closest('.category-card')) this.onCategoryCardClick(e);
        if (e.target.closest('.velora-accordion-header')) this.onAccordionClick(e);
        if (e.target.closest('.btn')) this.onBtnRipple(e);

        const link = e.target.closest('a[href="/shop/cart"]');
        if (link) {
            e.preventDefault();
            this.onCloseMobileMenu();
            this.onOpenCart();
        }

        const cartBtn = e.target.closest('.add-cart-btn, .add-cart-btn-text, #add_to_cart, .o_wsale_add_a_submit, .o_wish_add');
        const rmWishlistBtn = e.target.closest('.o_wish_rm');
        const wishlistBtn = e.target.closest('.wishlist-btn:not(.o_wish_rm), .o_add_wishlist');

        if (rmWishlistBtn) {
            e.preventDefault();
            e.stopPropagation();
            const article = rmWishlistBtn.closest('article');
            const wishId = rmWishlistBtn.dataset.wishId || article?.dataset.wishId;
            const productId = parseInt(article?.dataset.productId);
            if (wishId) {
                rpc(`/shop/wishlist/remove/${wishId}`).then(() => {
                    if (wishlistUtils && productId) {
                        wishlistUtils.removeWishlistProduct(productId);
                        wishlistUtils.updateWishlistNavBar();
                        wishlistUtils.updateWishlistView();
                    }
                    article?.remove();
                    this.syncWishlistButtons();
                    this.showToast('Removed from wishlist');
                }).catch(() => {
                    this.showToast('Could not remove from wishlist');
                });
            }
            return;
        }

        if (cartBtn) {
            e.preventDefault();
            e.stopPropagation();
            const form = cartBtn.closest('form');
            const odooProductId = cartBtn.dataset.productId || form?.querySelector('input[name="product_id"]')?.value;
            const odooTemplateId = cartBtn.dataset.templateId || form?.querySelector('input[name="product_template_id"]')?.value;
            const qtyInput = form?.querySelector('input[name="add_qty"]');
            const quantity = qtyInput ? (parseInt(qtyInput.value) || 1) : 1;

            if (odooProductId) {
                const cartItemsEl = this.$('#cartItems');
                const existingItem = Array.from(cartItemsEl?.querySelectorAll('.cart-item') || []).find(
                    el => el.dataset.productId === String(odooProductId)
                );

                if (existingItem) {
                    const lineId = existingItem.dataset.lineId;
                    const qtySpan = existingItem.querySelector('.cart-item-controls span');
                    const currentQty = qtySpan ? parseInt(qtySpan.textContent) : 1;
                    this.updateCartQty(lineId, currentQty + quantity);
                    this.onOpenCart();
                } else {
                    const params = {
                        product_id: parseInt(odooProductId),
                        quantity: quantity,
                    };
                    if (odooTemplateId) {
                        params.product_template_id = parseInt(odooTemplateId);
                    }
                    this.jsonRpc('/shop/cart/add', params).then(data => {
                        this.$$('.js-cart-count').forEach(el => el.textContent = String(data.cart_quantity));
                        this.onOpenCart();

                        const wishArticle = cartBtn.closest('.o_wishlist_item');
                        if (wishArticle) {
                            const wishId = wishArticle.dataset.wishId;
                            const prodId = parseInt(wishArticle.dataset.productId || odooProductId);
                            if (wishId) {
                                rpc(`/shop/wishlist/remove/${wishId}`).then(() => {
                                    if (wishlistUtils) {
                                        wishlistUtils.removeWishlistProduct(prodId);
                                        wishlistUtils.updateWishlistNavBar();
                                        wishlistUtils.updateWishlistView();
                                    }
                                    wishArticle.remove();
                                    this.syncWishlistButtons();
                                });
                            }
                        }
                    }).catch(() => this.showToast('Could not add to cart'));
                }
            }

            cartBtn.classList.add('added');
            const icon = cartBtn.querySelector('i');
            if (icon) {
                const original = icon.className;
                icon.className = 'fa-solid fa-check';
                setTimeout(() => {
                    cartBtn.classList.remove('added');
                    icon.className = original;
                }, 1200);
            }
        }

        if (wishlistBtn) {
            e.preventDefault();
            e.stopPropagation();
            const form = wishlistBtn.closest('form');
            const odooProductId = parseInt(
                wishlistBtn.dataset.productProductId ||
                wishlistBtn.dataset.productId ||
                form?.querySelector('input[name="product_id"]')?.value
            );
            const odooTemplateId = parseInt(
                wishlistBtn.dataset.productTemplateId ||
                wishlistBtn.dataset.templateId ||
                form?.querySelector('input[name="product_template_id"]')?.value
            );

            if (odooProductId) {
                this.addToWishlist(wishlistBtn, odooProductId);
            } else if (odooTemplateId) {
                rpc('/sale/create_product_variant', {
                    product_template_id: odooTemplateId,
                    product_template_attribute_value_ids: [],
                }).then(id => {
                    if (id) {
                        wishlistBtn.dataset.productProductId = id;
                        this.addToWishlist(wishlistBtn, id);
                    }
                }).catch(() => {
                    this.showToast('Could not add to wishlist');
                });
            }
        }
    }

    onDocumentSubmit(e) {
        const newsletterForm = e.target.closest('.newsletter-form, #newsletterForm');
        if (newsletterForm) {
            e.preventDefault();
            e.stopPropagation();
            const btn = newsletterForm.querySelector('a.btn, button, .newsletter-submit-btn');
            this.submitNewsletter(newsletterForm, btn);
            return;
        }
        if (e.target.closest('#contactForm')) {
            const form = e.target.closest('#contactForm');
            if (form && !this.validateContactForm(form)) {
                e.preventDefault();
                e.stopImmediatePropagation();
                return;
            }
        }
    }

    onOpenCart() {
        const cartDrawer = this.$('#cartDrawer');
        const drawerBackdrop = this.$('#drawerBackdrop');
        cartDrawer?.classList.add('active');
        drawerBackdrop?.classList.add('active');
        cartDrawer?.setAttribute('aria-hidden', 'false');
        document.body.style.overflow = 'hidden';
        this.fetchCartData();
    }

    onCloseCart() {
        const cartDrawer = this.$('#cartDrawer');
        const drawerBackdrop = this.$('#drawerBackdrop');
        cartDrawer?.classList.remove('active');
        drawerBackdrop?.classList.remove('active');
        cartDrawer?.setAttribute('aria-hidden', 'true');
        document.body.style.overflow = '';
    }

    fetchCartData() {
        this.jsonRpc('/theme_velora/cart/data').then(data => {
            this.renderCartDrawer(data);
        }).catch(() => {
            const cartItemsEl = this.$('#cartItems');
            if (cartItemsEl) cartItemsEl.innerHTML = '<p class="empty-state">Could not load cart.</p>';
        });
    }

    renderCartDrawer(data) {
        const { items, subtotal, cart_quantity, currency_symbol, currency_position } = data;
        const cartItemsEl = this.$('#cartItems');
        const cartTotalEl = this.$('#cartTotal');

        this.$$('.js-cart-count').forEach(el => el.textContent = String(cart_quantity));

        if (cartTotalEl) {
            cartTotalEl.textContent = this.formatCurrency(subtotal, currency_symbol, currency_position);
        }

        if (!cartItemsEl) return;

        if (!items || items.length === 0) {
            cartItemsEl.innerHTML = '<p class="empty-state">Your bag is empty. Discover a scent worth carrying.</p>';
            return;
        }

        cartItemsEl.innerHTML = items.map(item => `
            <div class="cart-item" data-line-id="${item.line_id}" data-product-id="${item.product_id}">
                <img src="${item.image_url}" alt="${item.name}" loading="lazy">
                <div class="cart-item-info">
                    <h4>${item.name}</h4>
                    <span>${this.formatCurrency(item.price, currency_symbol, currency_position)} &times; ${item.quantity}</span>
                </div>
                <div class="cart-item-controls">
                    <button class="qty-decrease" aria-label="Decrease quantity">&minus;</button>
                    <span>${item.quantity}</span>
                    <button class="qty-increase" aria-label="Increase quantity">+</button>
                    <button class="cart-item-remove" aria-label="Remove item"><i class="fa-solid fa-trash"></i></button>
                </div>
            </div>
        `).join('');

        this.$$('.qty-decrease', cartItemsEl).forEach(btn =>
            btn.addEventListener('click', (e) => {
                const lineId = e.target.closest('.cart-item').dataset.lineId;
                const currentQty = parseInt(e.target.closest('.cart-item-controls').querySelector('span').textContent);
                this.updateCartQty(lineId, currentQty - 1);
            })
        );
        this.$$('.qty-increase', cartItemsEl).forEach(btn =>
            btn.addEventListener('click', (e) => {
                const lineId = e.target.closest('.cart-item').dataset.lineId;
                const currentQty = parseInt(e.target.closest('.cart-item-controls').querySelector('span').textContent);
                this.updateCartQty(lineId, currentQty + 1);
            })
        );
        this.$$('.cart-item-remove', cartItemsEl).forEach(btn =>
            btn.addEventListener('click', (e) => {
                const lineId = e.target.closest('.cart-item').dataset.lineId;
                this.removeCartItem(lineId);
            })
        );
    }

    updateCartQty(lineId, quantity) {
        this.jsonRpc('/theme_velora/cart/update_qty', { line_id: lineId, quantity: quantity })
            .then(data => this.renderCartDrawer(data));
    }

    removeCartItem(lineId) {
        this.jsonRpc('/theme_velora/cart/remove', { line_id: lineId })
            .then(data => this.renderCartDrawer(data));
    }

    onCategoryCardClick(e) {
        const card = e.target.closest('.category-card');
        if (!card) return;
        const note = card.dataset.note || '';
        this.showToast(`Exploring ${note} fragrances`);
        const href = card.getAttribute('href');
        if (card.tagName === 'A' && href && href !== '#') {
            return;
        }
        const targetUrl = card.dataset.categoryUrl || `/theme_velora/category/${encodeURIComponent(note)}`;
        if (targetUrl) {
            setTimeout(() => {
                window.location.href = targetUrl;
            }, 250);
        }
    }

    initObservers() {
        const revealItems = this.$$('.reveal');
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

        const statNumbers = this.$$('.stat-number');
        const statObserver = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        this.animateCount(entry.target);
                        statObserver.unobserve(entry.target);
                    }
                });
            },
            { threshold: 0.5 }
        );
        statNumbers.forEach((el) => statObserver.observe(el));
    }

    animateCount(el) {
        const target = parseInt(el.dataset.count, 10);
        const duration = 1800;
        const startTime = performance.now();

        function tick(now) {
            const progress = Math.min((now - startTime) / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3);
            const value = Math.floor(eased * target);
            el.textContent = value.toLocaleString();
            if (progress < 1) {
                requestAnimationFrame(tick);
            } else {
                el.textContent = target.toLocaleString();
            }
        }
        requestAnimationFrame(tick);
    }

    initTestimonials() {
        const testimonialTrack = this.$('#testimonialTrack');
        const testimonialDots = this.$('#testimonialDots');
        const testimonialWrap = this.$('.testimonial-track-wrap');

        if (testimonialTrack && testimonialDots) {
            const cards = this.$$('.testimonial-card', testimonialTrack);
            let activeIndex = 0;

            const goToTestimonial = (index) => {
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
                dot.addEventListener('click', () => goToTestimonial(i));
                testimonialDots.appendChild(dot);
            });

            const dotEls = this.$$('button', testimonialDots);
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

            const prefersReducedMotionTestimonials = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
            const AUTOPLAY_DELAY = 5000;
            let autoplayTimer = null;

            const startAutoplay = () => {
                if (prefersReducedMotionTestimonials) return;
                stopAutoplay();
                autoplayTimer = setInterval(() => goToTestimonial(activeIndex + 1), AUTOPLAY_DELAY);
            };
            const stopAutoplay = () => clearInterval(autoplayTimer);

            (testimonialWrap || testimonialTrack).addEventListener('mouseenter', stopAutoplay);
            (testimonialWrap || testimonialTrack).addEventListener('mouseleave', startAutoplay);
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
            sectionVisibilityObserver.observe(testimonialWrap || testimonialTrack);

            testimonialTrack.addEventListener('scroll', this.updateEdgeFades, { passive: true });
            window.addEventListener('resize', this.updateEdgeFades);
            this.updateEdgeFades();
        }
    }

    updateEdgeFades() {
        const testimonialTrack = this.$('#testimonialTrack');
        const testimonialWrap = this.$('.testimonial-track-wrap');
        if (!testimonialWrap || !testimonialTrack) return;
        const maxScroll = testimonialTrack.scrollWidth - testimonialTrack.clientWidth;
        testimonialWrap.classList.toggle('show-left-fade', testimonialTrack.scrollLeft > 8);
        testimonialWrap.classList.toggle('show-right-fade', testimonialTrack.scrollLeft < maxScroll - 8);
    }

    onAccordionClick(e) {
        const header = e.target.closest('.velora-accordion-header');
        if (!header) return;
        const panel = header.nextElementSibling;
        const isOpen = header.getAttribute('aria-expanded') === 'true';

        this.$$('.velora-accordion-header').forEach((h) => {
            h.setAttribute('aria-expanded', 'false');
            if (h.nextElementSibling) {
                h.nextElementSibling.style.maxHeight = null;
                h.nextElementSibling.style.paddingBottom = '0';
            }
        });

        if (!isOpen) {
            header.setAttribute('aria-expanded', 'true');
            if (panel) {
                panel.style.maxHeight = `${panel.scrollHeight}px`;
            }
        }
    }

    submitNewsletter(form, btn) {
        if (!form) return;
        const emailInput = form.querySelector('input[type="email"], #newsletterEmail, .newsletter-email');
        const formMessage = form.parentNode?.querySelector('.form-message, #formMessage') || form.querySelector('.form-message, #formMessage');
        if (!emailInput) return;

        const email = emailInput.value.trim();
        const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;

        if (!emailPattern.test(email)) {
            emailInput.classList.add('is-invalid');
            if (formMessage) {
                formMessage.textContent = 'Please enter a valid email address.';
                formMessage.style.color = '#dc3545';
            }
            this.showToast('Please enter a valid email address.');
            emailInput.focus();
            return;
        }

        emailInput.classList.remove('is-invalid');
        if (formMessage) {
            formMessage.textContent = `Thank you! ${email} has joined the Velora Circle.`;
            formMessage.style.color = '';
        }
        this.showToast('Subscribed successfully');

        // Optional backend sync
        rpc('/theme_velora/newsletter/subscribe', { email }).catch(() => {});

        // Determine destination redirect URL
        let redirectUrl = btn?.getAttribute('href') || btn?.dataset?.redirect || form?.dataset?.successPage || form?.getAttribute('action') || '/contactus-thank-you';
        if (!redirectUrl || redirectUrl === '#' || redirectUrl.startsWith('javascript:')) {
            redirectUrl = form?.dataset?.successPage || form?.getAttribute('action') || '/contactus-thank-you';
        }
        if (!redirectUrl || redirectUrl === '#' || redirectUrl.startsWith('javascript:')) {
            redirectUrl = '/contactus-thank-you';
        }

        setTimeout(() => {
            window.location.href = redirectUrl;
        }, 350);
    }

    onNewsletterSubmit(e) {
        const form = e?.target?.closest('.newsletter-form, #newsletterForm') || this.$('#newsletterForm');
        const btn = form?.querySelector('a.btn, button, .newsletter-submit-btn');
        this.submitNewsletter(form, btn);
    }



    validateContactField(input) {
        const field = input.closest('.form-field, .s_website_form_field');
        let isValid = true;
        const val = input.value.trim();

        if (input.required && !val) {
            isValid = false;
        } else if (input.type === 'email' && val) {
            const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
            isValid = emailRegex.test(val);
        } else if (input.type === 'tel' && val) {
            const phoneRegex = /^\+?[0-9\s().-]{7,25}$/;
            isValid = phoneRegex.test(val);
        } else if (input.minLength && input.minLength > 0 && val.length < input.minLength) {
            isValid = false;
        } else if (!input.checkValidity()) {
            isValid = false;
        }

        if (!isValid) {
            input.classList.add('is-invalid');
            field?.classList.add('o_has_error');
        } else {
            input.classList.remove('is-invalid');
            if (field) {
                const otherInvalid = field.querySelectorAll('.is-invalid');
                if (otherInvalid.length === 0) {
                    field.classList.remove('o_has_error');
                }
            }
        }
        return isValid;
    }

    validateContactForm(form) {
        if (!form) return true;
        const inputs = Array.from(form.querySelectorAll('.s_website_form_input:not([type="hidden"])'));
        let firstInvalid = null;
        let isFormValid = true;

        inputs.forEach(input => {
            const valid = this.validateContactField(input);
            if (!valid) {
                isFormValid = false;
                if (!firstInvalid) firstInvalid = input;
            }
        });

        if (!isFormValid && firstInvalid) {
            firstInvalid.focus();
            firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
            this.showToast('Please correct the highlighted fields.');
        }

        return isFormValid;
    }

    onBtnRipple(e) {
        const btn = e.target.closest('.btn');
        if (!btn) return;
        const rect = btn.getBoundingClientRect();
        const ripple = document.createElement('div');
        const size = Math.max(rect.width, rect.height);
        ripple.className = 'ripple';
        ripple.style.width = ripple.style.height = `${size}px`;
        ripple.style.left = `${e.clientX - rect.left - size / 2}px`;
        ripple.style.top = `${e.clientY - rect.top - size / 2}px`;
        btn.appendChild(ripple);
        setTimeout(() => ripple.remove(), 600);
    }
}

registry
    .category("public.interactions")
    .add("theme_velora.interaction", ThemeVeloraInteraction);
