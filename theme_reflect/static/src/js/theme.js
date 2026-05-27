/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.ReflectThemeInteractivity = publicWidget.Widget.extend({
    selector: '#wrapwrap',
    events: {
        'click .pd-acc-trigger': '_onAccordionTriggerClick',
        'click .thumb-item': '_onThumbnailClick',
        'click .mobile-menu-btn': '_onMobileMenuClick',
        'click .reflect-cart-toggle': '_onCartToggleClick',
        'click .close-cart-sidebar': '_onCartCloseClick',
        'click #reflect_cart_backdrop': '_onCartCloseClick',
        'click .sidebar-qty-btn': '_onSidebarQtyClick',
        'click .remove-cart-item': '_onRemoveCartItemClick',
        'click .reflect-qty-btn-add': '_onProductQtyAdd',
        'click .reflect-qty-btn-sub': '_onProductQtySub',
        'click #reflect_add_to_cart': '_onAddToCartRedirect',
        // Toolbar attribute filter checkboxes
        'change .reflect-attr-check': '_onToolbarAttrCheck',
    },

    /**
     * @override
     */
    start() {
        this._super.apply(this, arguments);
        this._initStickyHeader();
        this._initScrollReveal();
        this._initReflectSidebar();
        this._bindReflectSidebarOffcanvas();
        this._initProductAccordions(); // ← open first accordion on page load
        this._bindWishlistSidecartHandler();

        // Check for ?open_cart=1 to auto-open sidebar (used by checkout "Return to Cart" link)
        const params = new URLSearchParams(window.location.search);
        if (params.get("open_cart") === "1") {
            this._openCartSidebar();
            // Clean up URL without reload
            const newUrl = window.location.pathname + window.location.search.replace(/[?&]open_cart=1(&|$)/, '$1').replace(/[?&]$/, '');
            window.history.replaceState({}, '', newUrl);
        }
    },

    _bindWishlistSidecartHandler() {
        if (window.__reflectWishlistSidecartBound) {
            return;
        }
        window.__reflectWishlistSidecartBound = true;

        document.addEventListener('click', (ev) => {
            const button = ev.target.closest('.wishlist-section .o_wish_add');
            if (!button) {
                return;
            }
            ev.preventDefault();
            ev.stopImmediatePropagation();
            this._onWishlistAddToSidecart(button);
        }, true);
    },

    _initReflectSidebar(root = document) {
        root.querySelectorAll('.rs-section-btn').forEach((btn) => {
            if (btn.dataset.rsInit === '1') {
                return;
            }
            btn.dataset.rsInit = '1';

            const targetId = btn.getAttribute('data-rs-target');
            const body = document.getElementById(targetId);
            if (!body) {
                return;
            }

            body.classList.add('rs-open');
            btn.classList.add('rs-open');

            btn.addEventListener('click', (ev) => {
                ev.preventDefault();
                const isOpen = body.classList.contains('rs-open');
                body.classList.toggle('rs-open', !isOpen);
                btn.classList.toggle('rs-open', !isOpen);
            });
        });
    },

    _bindReflectSidebarOffcanvas() {
        if (window.__reflectSidebarOffcanvasBound) {
            return;
        }
        window.__reflectSidebarOffcanvasBound = true;

        document.addEventListener('shown.bs.offcanvas', (ev) => {
            if (ev.target.id === 'offcanvasFilters') {
                this._initReflectSidebar(ev.target);
            }
        });
    },

    // ─── 1. Accordion Sidebar & Product Accordions ──────────────────────────

    /**
     * On page load: open the first .pd-acc-item that already has .active
     * (set in QWeb template) and set its icon to −.
     * All others stay closed with + icon.
     */
    _initProductAccordions() {
        this.$(".pd-acc-item").each((i, el) => {
            const item = $(el);
            const content = item.find(".pd-acc-content");
            const icon = item.find(".acc-icon");

            if (item.hasClass("active")) {
                // Snap open without animation on load
                content.css("max-height", content[0].scrollHeight + "px");
                icon.html("&#8722;"); // −
            } else {
                content.css("max-height", "");
                icon.html("&#43;");   // +
            }
        });
    },

    _onAccordionTriggerClick(ev) {
        const trigger = $(ev.currentTarget);
        const item = trigger.closest(".accordion-item, .pd-acc-item");
        if (!item.length) return;

        const isProductAcc = item.hasClass("pd-acc-item");
        const isOpen = item.hasClass("open") || item.hasClass("active");

        if (isProductAcc) {
            // Close all product accordions and reset their icons to +
            this.$(".pd-acc-item").each((i, el) => {
                const it = $(el);
                it.removeClass("active");
                it.find(".pd-acc-content").css("max-height", "");
                it.find(".acc-icon").html("&#43;"); // +
            });

            // If the clicked one was closed, open it and set icon to −
            if (!isOpen) {
                item.addClass("active");
                const content = item.find(".pd-acc-content");
                content.css("max-height", content[0].scrollHeight + "px");
                item.find(".acc-icon").html("&#8722;"); // −
            }
        } else {
            // Sidebar accordion — unchanged logic
            item.toggleClass("open", !isOpen);
            const icon = trigger.find(".accordion-icon");
            if (icon.length) icon.html(isOpen ? "&#8964;" : "&#8963;");
        }
    },

    // ─── 2. Product Thumbnails ──────────────────────────────────────────────
    _onThumbnailClick(ev) {
        const thumb = $(ev.currentTarget);
        const mainImg = this.$(".product_detail_img");
        const thumbImg = thumb.find("img");
        if (mainImg.length && thumbImg.length) {
            mainImg.css("opacity", "0");
            setTimeout(() => {
                mainImg.attr("src", thumbImg.attr("src").replace("image_128", "image_1024"));
                mainImg.css("opacity", "1");
            }, 200);
            this.$(".thumb-item").removeClass("active");
            thumb.addClass("active");
        }
    },

    // ─── 3. Sticky header ───────────────────────────────────────────────────
    _initStickyHeader() {
        const header = this.$("header");
        if (header.length) {
            $(window).on("scroll.reflect", () => {
                header.toggleClass("active", $(window).scrollTop() > 20);
            });
        }
    },

    // ─── 4. Mobile menu ─────────────────────────────────────────────────────
    _onMobileMenuClick() {
        this.$(".mobile-nav").toggleClass("active");
    },

    // ─── 5. Scroll-reveal ───────────────────────────────────────────────────
    _initScrollReveal() {
        const revealEls = this.$(".cat-card, .product-card, .story-card, .feature-card");
        if ("IntersectionObserver" in window && revealEls.length) {
            const observer = new IntersectionObserver((entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add("reflect-visible");
                        observer.unobserve(entry.target);
                    }
                });
            }, { threshold: 0.1 });
            revealEls.each((i, el) => {
                el.classList.add("reflect-hidden");
                observer.observe(el);
            });
        }
    },

    // ─── 6. Cart Sidebar ────────────────────────────────────────────────────
    _onCartToggleClick(ev) {
        ev.preventDefault();
        ev.stopImmediatePropagation();
        this._openCartSidebar();
    },

    _onCartCloseClick() {
        this.$("#reflect_cart_sidebar, #reflect_cart_backdrop").removeClass("open");
        this._unlockPageScrollForCart();
    },

    _openCartSidebar() {
        const sidebar = this.$("#reflect_cart_sidebar");
        const backdrop = this.$("#reflect_cart_backdrop");
        if (sidebar.length && backdrop.length) {
            this._lockPageScrollForCart();
            sidebar.addClass("open");
            backdrop.addClass("open");
            this._updateCartSidebar();
        } else {
            console.warn("Custom Cart Sidebar elements not found, using default.");
        }
    },

    _lockPageScrollForCart() {
        if (document.body.classList.contains("reflect-cart-scroll-lock")) {
            return;
        }
        const scrollY = window.scrollY || window.pageYOffset || 0;
        document.body.dataset.reflectCartScrollY = String(scrollY);
        document.body.classList.add("reflect-cart-scroll-lock");
        document.body.style.top = `-${scrollY}px`;
    },

    _unlockPageScrollForCart() {
        if (!document.body.classList.contains("reflect-cart-scroll-lock")) {
            return;
        }
        const scrollY = parseInt(document.body.dataset.reflectCartScrollY || "0", 10);
        document.body.classList.remove("reflect-cart-scroll-lock");
        document.body.style.top = "";
        delete document.body.dataset.reflectCartScrollY;
        window.scrollTo(0, Number.isNaN(scrollY) ? 0 : scrollY);
    },

    async _updateCartSidebar() {
        const listContainer = this.$("#cart_sidebar_list");
        const loading = this.$("#cart_sidebar_loading");

        if (!listContainer.length) return;

        loading.removeClass("d-none");

        try {
            const res = await fetch("/shop/cart");
            const html = await res.text();
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, "text/html");

            const rows = doc.querySelectorAll(".o_cart_product");
            let totalHtml = doc.querySelector("tr[name='o_order_total'] strong.monetary_field")?.innerHTML
                || doc.querySelector(".js_cart_summary #order_total .oe_currency_value")?.parentElement.innerHTML
                || "$0.00";
            let totalQty = 0;

            listContainer.empty();
            if (!rows || rows.length === 0) {
                listContainer.html("<div class='text-center py-5'><p class='text-muted'>Your cart is empty</p><a href='/shop' class='btn btn-dark mt-3'>Start Shopping</a></div>");
            } else {
                rows.forEach(row => {
                    const qtyInput = row.querySelector("input.js_quantity");
                    const id = qtyInput?.getAttribute("data-line-id") || row.getAttribute("data-line-id");
                    if (!id) return;

                    const productTitle = row.querySelector("h6")?.innerText || row.querySelector("strong")?.innerText || "Product";
                    const imgUrl = row.querySelector("img")?.src || "";
                    const qtyValue = qtyInput?.value || 1;
                    const price = row.querySelector("[name='website_sale_cart_line_price'] .oe_currency_value")?.innerText
                        || row.querySelector(".oe_price .oe_currency_value")?.innerText
                        || row.querySelector(".oe_currency_value")?.innerText || "0.00";
                    const symbol = row.querySelector("[name='website_sale_cart_line_price'] .oe_currency_symbol")?.innerText
                        || row.querySelector(".oe_price .oe_currency_symbol")?.innerText
                        || row.querySelector(".oe_currency_symbol")?.innerText || "$";
                    const desc = "";

                    totalQty += parseInt(qtyValue);

                    const itemHtml = `
                        <div class="cart-item-row" data-line-id="${id}">
                            <div class="cart-item-img">
                                <img src="${imgUrl}" alt="${productTitle}">
                            </div>
                            <div class="cart-item-info">
                                <div class="cart-item-title-row">
                                    <span class="cart-item-title">${productTitle}</span>
                                    <span class="cart-item-price">${symbol}${price}</span>
                                </div>
                                <div class="cart-item-desc">${desc}</div>
                                <div class="cart-item-actions">
                                    <div class="sidebar-qty-selector">
                                        <button class="sidebar-qty-btn minus" data-line-id="${id}">-</button>
                                        <input type="text" value="${qtyValue}" readonly>
                                        <button class="sidebar-qty-btn plus" data-line-id="${id}">+</button>
                                    </div>
                                    <button class="remove-cart-item fw-bold" data-line-id="${id}">Remove</button>
                                </div>
                            </div>
                        </div>
                    `;
                    listContainer.append(itemHtml);
                });
            }

            this.$(".sidebar-cart-total").html(totalHtml);
            this.$(".sidebar-cart-count, .o_wsale_cart_quantity").text(totalQty);

        } catch (err) {
            console.error("Cart Update Error:", err);
            listContainer.html("<p class='text-danger text-center'>Error loading cart</p>");
        } finally {
            loading.addClass("d-none");
        }
    },

    async _onSidebarQtyClick(ev) {
        const btn = $(ev.currentTarget);
        const lineId = btn.attr("data-line-id");
        const qtyChange = btn.hasClass("plus") ? 1 : -1;

        const input = btn.siblings('input');
        const currentQty = parseInt(input.val()) || 1;
        const newQty = Math.max(0, currentQty + qtyChange);

        await this._updateCartService(lineId, newQty);
    },

    async _onRemoveCartItemClick(ev) {
        const btn = $(ev.currentTarget);
        const lineId = btn.attr("data-line-id");
        await this._updateCartService(lineId, 0);
    },

    async _updateCartService(lineId, quantity) {
        const params = {
            line_id: parseInt(lineId, 10),
            quantity: quantity
        };

        try {
            await fetch("/shop/cart/update", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ jsonrpc: "2.0", method: "call", params: params })
            });
            this._updateCartSidebar();
        } catch (err) {
            console.error("Cart Service Update Error:", err);
        }
    },

    // ─── 7. Toolbar Attribute Filter (shop / accessories / category page) ───────
    /**
     * When a toolbar checkbox changes, collect all checked attribute value IDs
     * and rebuild the URL using Odoo's standard `attrib` query param format:
     *   /shop?attrib=ATTR_ID-VALUE_ID&attrib=ATTR_ID-VALUE_ID2 ...
     * This matches exactly what the Odoo sidebar filters do, so both
     * the toolbar dropdowns and any sidebar stay in sync.
     */
    _onToolbarAttrCheck(ev) {
        const allChecked = this.$('.reflect-attr-check:checked');
        const url = new URL(window.location.href);

        // Remove all existing attrib params
        url.searchParams.delete('attrib');

        allChecked.each((i, el) => {
            const attribId = $(el).data('attrib-id');
            const valueId = $(el).data('value-id');
            if (attribId && valueId) {
                // Odoo format: attrib=ATTRIB_ID-VALUE_ID
                url.searchParams.append('attrib', attribId + '-' + valueId);
            }
        });

        // Reset to page 1 when filters change
        url.searchParams.delete('page');

        window.location.href = url.toString();
    },

    // ─── 8. Product Page Quantity & Custom Add To Cart ────────────────────────
    _onProductQtyAdd(ev) {
        if (ev) ev.preventDefault();
        const input = this.$(".reflect-qty-input");
        let val = parseInt(input.val()) || 1;
        input.val(++val).trigger('change');
    },

    _onProductQtySub(ev) {
        if (ev) ev.preventDefault();
        const input = this.$(".reflect-qty-input");
        let val = parseInt(input.val()) || 1;
        if (val > 1) {
            input.val(--val).trigger('change');
        }
    },

    async _onAddToCartRedirect(ev) {
        ev.preventDefault();
        ev.stopImmediatePropagation();

        const form = $(ev.currentTarget).closest('form');
        const productId = parseInt(form.find('input[name="product_id"]').val(), 10);
        const templateId = parseInt(form.find('input[name="product_template_id"]').val(), 10);
        const qty = parseInt(form.find('input[name="add_qty"]').val(), 10) || 1;

        if (!productId || !templateId) return;

        try {
            await fetch('/shop/cart/add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    jsonrpc: "2.0",
                    method: "call",
                    params: {
                        product_template_id: templateId,
                        product_id: productId,
                        quantity: qty
                    }
                })
            });
            this._openCartSidebar();
        } catch (err) {
            console.error("Cart Add Error:", err);
        }
    },

    _updateWishlistNavbarQuantity(productIdToRemove) {
        let wishlistIds = [];
        try {
            wishlistIds = JSON.parse(window.sessionStorage.getItem('wishlist_product_ids') || '[]');
        } catch {
            wishlistIds = [];
        }

        if (productIdToRemove) {
            wishlistIds = wishlistIds.filter((id) => id !== productIdToRemove);
            window.sessionStorage.setItem('wishlist_product_ids', JSON.stringify(wishlistIds));
        }

        document.querySelectorAll('.o_wsale_my_wish .my_wish_quantity').forEach((badge) => {
            badge.textContent = `${wishlistIds.length}`;
            badge.classList.toggle('d-none', !wishlistIds.length);
        });
    },

    _updateWishlistPageEmptyState() {
        const visibleItems = document.querySelectorAll('.wishlist-section article:not([style*="display: none"])');
        const emptyEl = document.getElementById('empty-wishlist-message');
        const tableEl = document.querySelector('.wishlist-section .o_wishlist_table');
        if (emptyEl) {
            emptyEl.classList.toggle('d-none', visibleItems.length > 0);
        }
        if (tableEl) {
            tableEl.classList.toggle('d-none', visibleItems.length === 0);
        }
    },

    async _onWishlistAddToSidecart(button) {
        const productId = parseInt(button.dataset.productProductId, 10);
        const templateId = parseInt(button.dataset.productTemplateId, 10);
        const article = button.closest('article');
        const wishId = parseInt(article?.dataset.wishId, 10);
        const productIdForWishlist = parseInt(article?.dataset.productId, 10) || productId;

        if (!productId || !templateId) {
            return;
        }

        try {
            await fetch('/shop/cart/add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    jsonrpc: "2.0",
                    method: "call",
                    params: {
                        product_template_id: templateId,
                        product_id: productId,
                        quantity: 1
                    }
                })
            });

            if (wishId) {
                await fetch(`/shop/wishlist/remove/${wishId}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        jsonrpc: "2.0",
                        method: "call",
                        params: {}
                    })
                });
            }

            if (article) {
                article.style.display = 'none';
            }
            this._updateWishlistNavbarQuantity(productIdForWishlist);
            this._updateWishlistPageEmptyState();
            this._openCartSidebar();
        } catch (err) {
            console.error("Wishlist Sidecart Add Error:", err);
        }
    }
});

export default publicWidget.registry.ReflectThemeInteractivity;
