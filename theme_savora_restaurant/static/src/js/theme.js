/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";
/**
 * Theme Savora — theme.js
 * Comprehensive logic for Sticky header, mobile menu, menu tabs, 
 * cart sidebar, scroll reveal, and multi-step reservation system.
 */
publicWidget.registry.SavoraTheme = publicWidget.Widget.extend({
    selector: '#wrapwrap',
    events: {
        'click .sv-tab': '_onTabClick',
        'click .menu-tab': '_onMenuTabClick',
        'click .sv-close-cart': '_onCloseCart',
        'click .savora-cart-toggle': '_onOpenCart',
        'click #restaurant_cart_backdrop': '_onCloseCart',
        'click .rs-section-btn': '_onSidebarAccordionClick',
        'click a[href^="#"]': '_onSmoothScroll',
        'click .js_check_product.a-submit': '_onAddToCartClick',
    },
    /**
     * @override
     */
    start() {
        this._initStickyHeader();
        this._initActiveNav();
        this._initScrollReveal();
        this._initCounters();
        this._initGalleryLightbox();
        this._initEditableDemoCheckoutFields();
        // Listen for Odoo's core cart update event
        $(document).on('cart_ready', () => {
            this._onOpenCart();
        });
        return this._super.apply(this, arguments);
    },
    /* ─── Shared Logic ─── */
    /**
     * Initializes the sticky header behavior on scroll.
     * @private
     */
    _initStickyHeader() {
        const header = document.getElementById('sv-header');
        if (!header) return;
        window.addEventListener('scroll', () => {
            if (window.scrollY > 50) header.classList.add('scrolled');
            else header.classList.remove('scrolled');
        });
    },
    /**
     * Marks the current navigation link as active based on the URL path.
     * @private
     */
    _initActiveNav() {
        const path = window.location.pathname;
        const links = document.querySelectorAll('.sv-nav-link, .sv-mobile-nav-link');
        links.forEach(link => {
            if (link.getAttribute('href') === path) {
                link.classList.add('active');
            }
        });
    },
    /**
     * Handles clicks on category tabs to filter items.
     * @private
     * @param {Event} ev
     */
    _onTabClick(ev) {
        const $tab = $(ev.currentTarget);
        const filter = String($tab.data('filter'));
        const $section = $tab.closest('.s_savora_menu');
        const $scope = $section.length ? $section : this.$el;
        $scope.find('.sv-tab').removeClass('active');
        $tab.addClass('active');
        $scope.find('.sv-mcard-col').each((i, el) => {
            const $card = $(el);
            if (String($card.data('filter')) === filter) {
                $card.show().css('animation', 'fadeInUp 0.6s ease forwards');
            } else {
                $card.hide();
            }
        });
    },
    /**
     * Handles clicks on menu category tabs.
     * @private
     * @param {Event} ev
     */
    _onMenuTabClick(ev) {
        const $tab = $(ev.currentTarget);
        const filter = String($tab.attr('data-f'));
        // Global selection to ensure it works across different snippets/containers
        $('.menu-tab').removeClass('active');
        $(`.menu-tab[data-f="${filter}"]`).addClass('active');
        $('.menu-category').each((i, el) => {
            const $cat = $(el);
            if (String($cat.attr('data-c')) === filter) {
                $cat.fadeIn(400);
            } else {
                $cat.hide();
            }
        });
    },
    /* ─── Cart ─── */
    /**
     * Opens the cart sidebar after a product is added.
     * @private
     */
    _onAddToCartClick() {
        // Fallback: Open cart after a small delay if the event doesn't fire immediately
        setTimeout(() => {
            this._onOpenCart();
        }, 800);
    },
    /**
     * Opens the cart sidebar and overlays.
     * @private
     */
    _onOpenCart(ev) {
        if (ev) {
            ev.preventDefault();
        }
        this.$('#savora_cart_sidebar').addClass('open');
        this.$('#restaurant_cart_backdrop').addClass('open');
        document.body.style.overflow = 'hidden';
        this._loadCartData();
    },
    /**
     * Closes the cart sidebar and overlays.
     * @private
     */
    _onCloseCart() {
        this.$('#savora_cart_sidebar').removeClass('open');
        this.$('#restaurant_cart_backdrop').removeClass('open');
        document.body.style.overflow = '';
    },
    /**
     * Fetches and renders cart data in the sidebar.
     * @private
     */
    _loadCartData() {
        const $list = this.$('#sv_cart_list');
        const $loading = this.$('#sv_cart_loading');
        if (!$list.length) return;
        $loading.removeClass('d-none');
        $list.empty();
        fetch('/shop/cart', {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
        .then(r => r.text())
        .then(html => {
            $loading.addClass('d-none');
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const cartProducts = doc.querySelectorAll('#cart_products .o_cart_product');
            let totalQty = 0;
            if (cartProducts.length > 0) {
                cartProducts.forEach(el => {
                    const name = el.querySelector('a[name="o_cart_line_product_link"] h6')?.textContent.trim() || 'Product';
                    // Extract variant attributes and descriptions specifically, ignoring action buttons
                    const attrEl = el.querySelector('.d-inline-flex .text-muted');
                    const descEl = el.querySelector('.text-muted.small span');
                    let desc = '';
                    if (attrEl) {
                        const attrText = attrEl.textContent.trim().replace(/^-/, '').trim();
                        if (attrText && attrText !== '-') {
                            desc += attrText;
                        }
                    }
                    if (descEl) {
                        const descText = descEl.textContent.trim();
                        if (descText) {
                            desc += (desc ? ', ' : '') + descText;
                        }
                    }
                    const imgEl = el.querySelector('.o_cart_product_image img');
                    const imgUrl = imgEl ? imgEl.getAttribute('src') : '';
                    const priceEl = el.querySelector('[name="website_sale_cart_line_price"]');
                    const priceText = priceEl ? priceEl.textContent.trim().replace(/\s+/g, ' ') : '';
                    const qtyEl = el.querySelector('input.js_quantity');
                    const qtyVal = qtyEl ? parseInt(qtyEl.getAttribute('value') || qtyEl.value || '1', 10) : 1;
                    totalQty += qtyVal;
                    const $itemHtml = $(`
                        <div class="sv-cart-item">
                            <div class="sv-cart-item-img">
                                <img src="${imgUrl}" alt="${name}"/>
                            </div>
                            <div class="sv-cart-item-info">
                                <div class="sv-cart-item-name">${name}${desc ? ' (' + desc + ')' : ''}</div>
                                <div class="sv-cart-item-qty">Qty: ${qtyVal}</div>
                                <div class="sv-cart-item-price">${priceText}</div>
                            </div>
                        </div>
                    `);
                    $list.append($itemHtml);
                });
                const subtotalEl = doc.querySelector('tr[name="o_order_total_untaxed"] .monetary_field') || doc.querySelector('tr[name="o_order_total"] .monetary_field');
                const subtotalVal = subtotalEl ? subtotalEl.textContent.trim().replace(/\s+/g, ' ') : '$0.00';
                this.$('.sv-sidebar-cart-total').text(subtotalVal);
            } else {
                $list.append('<div class="sv-cart-empty"><i class="fa fa-shopping-bag"></i><p>Your cart is empty.</p></div>');
                this.$('.sv-sidebar-cart-total').text('$0.00');
            }
            this.$('.sv-sidebar-cart-count').text(totalQty);
            const $navQty = $('.my_cart_quantity');
            if ($navQty.length) {
                if (totalQty === 0) {
                    $navQty.addClass('d-none');
                } else {
                    $navQty.text(totalQty).removeClass('d-none');
                }
            }
        });
    },
    /* ─── UI Utilities ─── */
    /**
     * Initializes scroll reveal animations using IntersectionObserver.
     * @private
     */
    _initScrollReveal() {
        const els = document.querySelectorAll('.sv-reveal');
        if (!els.length || !('IntersectionObserver' in window)) return;
        const obs = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                    obs.unobserve(entry.target);
                }
            });
        }, { threshold: 0.12 });
        els.forEach(el => obs.observe(el));
    },
    /**
     * Handles accordion-style sidebar clicks in the restaurant sections.
     * @private
     * @param {Event} ev
     */
    _onSidebarAccordionClick(ev) {
        ev.preventDefault();
        const $btn = $(ev.currentTarget);
        const targetId = $btn.data('rs-target');
        const $body = $('#' + targetId);
        $body.toggleClass('rs-open');
        $btn.toggleClass('rs-open');
    },
    /**
     * Initializes number increment animations when visible.
     * @private
     */
    _initCounters() {
        this.$('.sv-num').each((i, el) => {
            const $el = $(el);
            const target = parseInt($el.text().replace(/[^0-9]/g, ''), 10);
            if (isNaN(target)) return;
            const obs = new IntersectionObserver((entries) => {
                if (entries[0].isIntersecting) {
                    $({ countNum: 0 }).animate({ countNum: target }, {
                        duration: 1200,
                        step: function() { $el.text(Math.floor(this.countNum)); },
                        complete: function() { $el.text(target); }
                    });
                    obs.disconnect();
                }
            }, { threshold: 0.5 });
            obs.observe(el);
        });
    },
    /**
     * Handles smooth scrolling for internal anchor links.
     * @private
     * @param {Event} ev
     */
    _onSmoothScroll(ev) {
        const href = $(ev.currentTarget).attr('href');
        if (href === '#') return;
        const $target = $(href);
        if ($target.length) {
            ev.preventDefault();
            $('html, body').animate({
                scrollTop: $target.offset().top - 90
            }, 600);
        }
    },
    /**
     * Initializes the image gallery lightbox.
     * @private
     */
    _initGalleryLightbox() {
        const $lightbox = this.$('#sv_gallery_lightbox');
        if (!$lightbox.length) return;
        const $items = this.$('.sv-gallery-item');
        const $img = this.$('#sv_lightbox_img');
        const $caption = this.$('#sv_lightbox_caption');
        const $dots = this.$('#sv_lightbox_dots');
        let activeIndex = 0;
        const showImage = (index) => {
            if (!$items.length) return;
            activeIndex = (index + $items.length) % $items.length;
            const $item = $items.eq(activeIndex);
            const src = $item.data('src') || $item.find('img').attr('src');
            const caption = $item.data('caption') || $item.find('img').attr('alt') || '';
            $img.attr({
                src: src,
                alt: caption,
            });
            $caption.text(caption);
            $dots.find('.sv-lb-dot').removeClass('active').eq(activeIndex).addClass('active');
        };
        $dots.empty();
        $items.each((index) => {
            $('<button/>', {
                type: 'button',
                class: 'sv-lb-dot',
                'aria-label': `Show image ${index + 1}`,
            }).on('click', (ev) => {
                ev.stopPropagation();
                showImage(index);
            }).appendTo($dots);
        });
        this.$('.sv-gallery-item').on('click', (ev) => {
            showImage($items.index(ev.currentTarget));
            $lightbox.addClass('sv-lb-open');
            document.body.style.overflow = 'hidden';
        });
        this.$('#sv_lightbox_close').on('click', () => {
            $lightbox.removeClass('sv-lb-open');
            document.body.style.overflow = '';
        });
        this.$('#sv_lightbox_prev').on('click', (ev) => {
            ev.stopPropagation();
            showImage(activeIndex - 1);
        });
        this.$('#sv_lightbox_next').on('click', (ev) => {
            ev.stopPropagation();
            showImage(activeIndex + 1);
        });
        $lightbox.on('click', (ev) => {
            if (ev.target === $lightbox[0]) {
                $lightbox.removeClass('sv-lb-open');
                document.body.style.overflow = '';
            }
        });
    },
    /**
     * Allows editing the customer fields in Odoo's demo express checkout modal.
     *
     * The demo provider renders these fields readonly by default even though its
     * express checkout script reads their values for the shipping address.
     *
     * @private
     */
    _initEditableDemoCheckoutFields() {
        const unlockFields = () => {
            this.$('[id^="o_payment_demo_shipping_info_"] input').prop('readonly', false);
            this.$('[id^="o_payment_demo_shipping_info_"] select').prop('disabled', false);
        };
        unlockFields();
        this.$('[id^="o_payment_demo_modal_"]').on('shown.bs.modal', unlockFields);
    }
});
/**
 * Multi-step reservation widget for Theme Savora.
 * Handles the end-to-end reservation flow:
 * 1. Date and Time selection (via interactive calendar and slot fetching)
 * 2. Guest details entry
 * 3. Review of selection
 * 4. Final confirmation after RPC submission
 *
 * @extends publicWidget.Widget
 */
publicWidget.registry.SavoraReservations = publicWidget.Widget.extend({
    selector: '.sv-reservation-wrapper',
    events: {
        'click #toStep2': '_onToStep2',
        'click #backToStep1': '_onBackToStep1',
        'click #toStep3': '_onToStep3',
        'click #backToStep2': '_onBackToStep2',
        'click #toStep4': '_onToStep4',
        'click .sv-res-step': '_onSelectStep',
        'click .sv-cal-day': '_onSelectDay',
        'click .sv-res-time': '_onSelectTime',
        'click .fa-chevron-left': '_onPrevMonth',
        'click .fa-chevron-right': '_onNextMonth',
    },
    /**
     * @override
     */
    start() {
        /** @type {jQuery} Step 1 container (Date/Time) */
        this.$step1 = this.$('#reserveStep1');
        /** @type {jQuery} Step 2 container (Details) */
        this.$step2 = this.$('#reserveStep2');
        /** @type {jQuery} Step 3 container (Review) */
        this.$step3 = this.$('#reserveStep3');
        /** @type {jQuery} Step 4 container (Confirmation) */
        this.$step4 = this.$('#reserveStep4');
        /** @type {jQuery} Progress line for Step 1-2 */
        this.$line1 = this.$('#resLine1');
        /** @type {jQuery} Progress line for Step 2-3 */
        this.$line2 = this.$('#resLine2');
        /** @type {jQuery} Progress line for Step 3-4 */
        this.$line3 = this.$('#resLine3');
        /** @type {Date} The month currently being viewed in the calendar */
        this.currentViewDate = new Date();
        /** @type {Date} The specific date selected by the user */
        this.selectedDate = new Date();
        this._renderCalendar();
        return this._super.apply(this, arguments);
    },
    /**
     * Renders the reservation calendar grid based on currentViewDate.
     * @private
     */
    _renderCalendar() {
        const monthNames = ["JANUARY", "FEBRUARY", "MARCH", "APRIL", "MAY", "JUNE",
            "JULY", "AUGUST", "SEPTEMBER", "OCTOBER", "NOVEMBER", "DECEMBER"];
        const month = this.currentViewDate.getMonth();
        const year = this.currentViewDate.getFullYear();
        const today = new Date();
        this.$('#calMonthYear').text(`${monthNames[month]} ${year}`);
        const $grid = this.$('.sv-cal-grid');
        $grid.empty();
        const firstDay = new Date(year, month, 1).getDay();
        const daysInMonth = new Date(year, month + 1, 0).getDate();
        // Muted days from previous month
        const prevMonthLastDay = new Date(year, month, 0).getDate();
        for (let i = firstDay - 1; i >= 0; i--) {
            $grid.append(`<div class="sv-cal-day muted">${prevMonthLastDay - i}</div>`);
        }
        // Current month days
        for (let i = 1; i <= daysInMonth; i++) {
            let active = '';
            if (this.selectedDate.getDate() === i && 
                this.selectedDate.getMonth() === month && 
                this.selectedDate.getFullYear() === year) {
                active = 'active';
            }
            // Disable past days in current month
            let muted = '';
            if (year === today.getFullYear() && month === today.getMonth() && i < today.getDate()) {
                muted = 'muted';
            }
            $grid.append(`<div class="sv-cal-day ${active} ${muted}">${i}</div>`);
        }
        // Muted days from next month to fill 42 cells (6 rows)
        const totalCells = 42;
        const remainingCells = totalCells - (firstDay + daysInMonth);
        for (let i = 1; i <= remainingCells; i++) {
            $grid.append(`<div class="sv-cal-day muted">${i}</div>`);
        }
        this._updateSlots();
    },
    /**
     * Navigates to the previous month in the calendar.
     * @private
     */
    _onPrevMonth() {
        this.currentViewDate.setMonth(this.currentViewDate.getMonth() - 1);
        this._renderCalendar();
    },
    /**
     * Navigates to the next month in the calendar.
     * @private
     */
    _onNextMonth() {
        this.currentViewDate.setMonth(this.currentViewDate.getMonth() + 1);
        this._renderCalendar();
    },
    /**
     * Handles selection of party size steps.
     * @private
     * @param {Event} ev
     */
    _onSelectStep(ev) {
        this.$('.sv-res-step').removeClass('active');
        $(ev.currentTarget).addClass('active');
        this._updateReviewData();
    },
    /**
     * Handles selection of a day in the calendar.
     * @private
     * @param {Event} ev
     */
    _onSelectDay(ev) {
        const $day = $(ev.currentTarget);
        if ($day.hasClass('muted')) return;
        this.selectedDate = new Date(this.currentViewDate);
        this.selectedDate.setDate(parseInt($day.text().trim()));
        this.$('.sv-cal-day').removeClass('active');
        $day.addClass('active');
        this._updateSlots();
    },
    /**
     * Fetches available reservation slots for the selected date.
     * @private
     */
    _updateSlots() {
        const year = this.selectedDate.getFullYear();
        const month = (this.selectedDate.getMonth() + 1).toString().padStart(2, '0');
        const day = this.selectedDate.getDate().toString().padStart(2, '0');
        const dateVal = `${year}-${month}-${day}`;
        rpc('/reservations/get_slots', { date_str: dateVal }).then((data) => {
            const $times = this.$('.sv-res-times');
            $times.empty();
            if (data.available_times && data.available_times.length) {
                data.available_times.forEach((t, i) => {
                    const active = (i === 0) ? 'active' : '';
                    $times.append(`<div class="sv-res-time ${active}">${t}</div>`);
                });
            } else {
                $times.append('<p class="text-muted p-3">No available slots.</p>');
            }
            this._updateReviewData();
        });
    },
    /**
     * Handles selection of a time slot.
     * @private
     * @param {Event} ev
     */
    _onSelectTime(ev) {
        this.$('.sv-res-time').removeClass('active');
        $(ev.currentTarget).addClass('active');
        this._updateReviewData();
    },
    /**
     * Transitions from Step 1 (Date/Time) to Step 2 (Details).
     * @private
     */
    _onToStep2() {
        if (!this.$('.sv-res-time.active').length) {
            alert("Please select an available time slot.");
            return;
        }
        this.$step1.hide();
        this.$step2.show();
        this.$line2.addClass('active');
        this._updateReviewData();
    },
    /**
     * Transitions back from Step 2 to Step 1.
     * @private
     */
    _onBackToStep1() {
        this.$step2.hide();
        this.$step1.show();
        this.$line2.removeClass('active');
    },
    /**
     * Transitions from Step 2 (Details) to Step 3 (Review).
     * @private
     */
    _onToStep3() {
        const name = this.$('#resFirstName').val();
        const email = this.$('#resEmail').val();
        if (!name || !email) {
            alert("Please fill in your name and email.");
            return;
        }
        this._updateReviewData();
        this.$step2.hide();
        this.$step3.show();
        this.$line3.addClass('active');
    },
    /**
     * Transitions back from Step 3 to Step 2.
     * @private
     */
    _onBackToStep2() {
        this.$step3.hide();
        this.$step2.show();
        this.$line3.removeClass('active');
    },
    /**
     * Submits the reservation data and transitions to Step 4 (Confirmation).
     * @private
     */
    _onToStep4() {
        const year = this.selectedDate.getFullYear();
        const month = (this.selectedDate.getMonth() + 1).toString().padStart(2, '0');
        const day = this.selectedDate.getDate().toString().padStart(2, '0');
        const dateVal = `${year}-${month}-${day}`;
        const timeVal = this.$('.sv-res-time.active').text().trim();
        const guests = this.$('.sv-res-step.active').data('guests') || '2';
        const data = {
            name: this.$('#resFirstName').val() + " " + this.$('#resLastName').val(),
            email: this.$('#resEmail').val(),
            phone: this.$('#resPhone').val(),
            date: dateVal,
            time: timeVal,
            party_size: guests,
            notes: this.$('#resNotes').val(),
        };
        rpc('/reservations/submit', data).then((res) => {
            if (res.error) {
                alert("Error: " + res.error);
            } else {
                this.$step3.hide();
                this.$step4.show();
            }
        });
    },
    /**
     * Updates the summary data displayed in the review and confirmation steps.
     * @private
     */
    _updateReviewData() {
        const monthNames = ["January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"];
        const day = this.selectedDate.getDate();
        const month = monthNames[this.selectedDate.getMonth()];
        const year = this.selectedDate.getFullYear();
        const time = this.$('.sv-res-time.active').text() || '7:30 PM';
        const guests = this.$('.sv-res-step.active').text() || '2';
        const firstName = this.$('#resFirstName').val() || 'Jane';
        const lastName = this.$('#resLastName').val() || 'Doe';
        const email = this.$('#resEmail').val() || 'jane.doe@example.com';
        const phone = this.$('#resPhone').val() || '+1 (555) 019-9238';
        const notes = this.$('#resNotes').val() || 'None';
        const fullDate = `${month} ${year} ${day}`;
        this.$('#resReviewDate, #reviewDateVal, #confirmDateVal').text(fullDate);
        this.$('#resReviewTime, #reviewTimeVal, #confirmTimeVal').text(time);
        const guestLabel = this.$('.sv-res-step.active').data('guests') === 9 ? '9+ Guests' : guests + ' Guests';
        this.$('#resReviewGuests, #reviewGuestsVal, #confirmGuestsVal').text(guestLabel);
        this.$('#reviewNameVal, #confirmNameVal').text(firstName + " " + lastName);
        this.$('#reviewEmailVal').text(email);
        this.$('#reviewPhoneVal').text(phone);
        this.$('#reviewNotesVal').text(notes);
    }
});

export default publicWidget.registry.SavoraTheme;
