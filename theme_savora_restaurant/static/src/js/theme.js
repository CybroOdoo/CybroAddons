/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";
/**
 * Theme Restaurant — theme.js
 * High-compatibility version for Odoo 17 Community.
 */
const SavoraTheme = publicWidget.Widget.extend({
    selector: '#wrapwrap',
    events: {
        'click .sv-tab': '_onTabClick',
        'click .menu-tab': '_onMenuTabClick',
        'click .sv-close-cart': '_onCloseCart',
        'click .savora-cart-toggle': '_onOpenCart',
        'click #restaurant_cart_backdrop': '_onCloseCart',
        'click .rs-section-btn': '_onSidebarAccordionClick',
        'click a[href^="#"]': '_onSmoothScroll',
        'click .js_see_all_reviews': '_onSeeAllReviews',
        // Reservation Events
        'click #toStep2': '_onToStep2',
        'click #backToStep1': '_onBackToStep1',
        'click #toStep3': '_onToStep3',
        'click #backToStep2': '_onBackToStep2',
        'click #toStep4': '_onToStep4',
        'click .sv-res-step-btn': '_onSelectStep',
        'click .sv-cal-day': '_onSelectDay',
        'click .sv-res-time': '_onSelectTime',
        'click .sv-cal-prev': '_onPrevMonth',
        'click .sv-cal-next': '_onNextMonth',
    },
    /**
     * @override
     */
    start: function () {
        var self = this;
        this._super.apply(this, arguments);
        this._initStickyHeader();
        this._initActiveNav();
        this._initScrollReveal();
        this._initCounters();
        this._initGalleryLightbox();
        this._initSidebarAccordions();
        // Check for reservation wrapper
        if (this.$('.sv-reservation-wrapper').length) {
            this.currentViewDate = this._getToday();
            this.currentViewDate.setDate(1);
            this.selectedDate = this._getToday();
            this._renderCalendar();
        }
        // Auto-hide Review Success Alert
        const $successAlert = this.$('.alert-success');
        if ($successAlert.length) {
            setTimeout(() => {
                $successAlert.fadeOut(1000);
            }, 5000);
        }
        return Promise.resolve();
    },
    /* ─── UI Utilities ─── */
    /**
     * Initializes the sticky header effect on scroll.
     */
    _initStickyHeader: function () {
        const header = document.getElementById('top');
        if (!header) return;
        window.addEventListener('scroll', () => {
            if (window.scrollY > 50) header.classList.add('scrolled');
            else header.classList.remove('scrolled');
        });
    },
    /**
     * Highlights the active navigation link based on current URL path.
     */
    _initActiveNav: function () {
        const path = window.location.pathname;
        this.$('.sv-nav-link, .sv-mobile-nav-link').each(function() {
            if (this.getAttribute('href') === path) $(this).addClass('active');
        });
    },
    /**
     * Filters items based on the selected tab in category sections.
     * @param {Event} ev
     */
    _onTabClick: function (ev) {
        const filter = $(ev.currentTarget).data('filter');
        this.$('.sv-tab').removeClass('active');
        $(ev.currentTarget).addClass('active');
        this.$('.sv-mcard-col').each(function() {
            const productFilters = ($(this).attr('data-filter') || "").toString().split(' ');
            if (filter === 'all' || productFilters.includes(filter.toString())) $(this).show();
            else $(this).hide();
        });
    },
    /**
     * Switches between different menu categories on the menu page.
     * @param {Event} ev
     */
    _onMenuTabClick: function (ev) {
        const filter = $(ev.currentTarget).data('f');
        this.$('.menu-tab').removeClass('active');
        $(ev.currentTarget).addClass('active');
        this.$('.menu-category').each(function() {
            if ($(this).data('c') === filter) $(this).show();
            else $(this).hide();
        });
    },
    /**
     * Opens the shopping cart sidebar.
     */
    _onOpenCart: async function () {
        this.$('#savora_cart_sidebar, #restaurant_cart_backdrop').addClass('open');
        document.body.style.overflow = 'hidden';
        const $list = this.$('#sv_cart_list');
        const $loading = this.$('#sv_cart_loading');
        $list.empty();
        $loading.removeClass('d-none');
        try {
            const data = await jsonrpc('/savora/cart/data', {});
            $loading.addClass('d-none');
            if (data && data.lines && data.lines.length > 0) {
                let html = '';
                data.lines.forEach(line => {
                    html += `
                        <div class="d-flex align-items-center mb-3 p-3" style="background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.05); border-radius:4px;">
                            <img src="${line.image}" alt="${line.name}" style="width:60px; height:60px; object-fit:cover; border-radius:4px; margin-right:15px;"/>
                            <div class="flex-grow-1">
                                <h6 style="color:var(--sv-cream,#efe6db); margin-bottom:4px; font-size:14px;">${line.name}</h6>
                                <div class="d-flex justify-content-between align-items-center">
                                    <span style="color:var(--sv-muted,#9b8f85); font-size:13px;">Qty: ${line.qty}</span>
                                    <span style="color:var(--sv-gold,#c78b3a); font-weight:600; font-size:14px;">${line.price}</span>
                                </div>
                            </div>
                        </div>
                    `;
                });
                $list.html(html);
            } else {
                $list.html('<div class="text-center py-5"><p style="color:var(--sv-muted,#9b8f85);">Your cart is empty.</p></div>');
            }
            if (data) {
                this.$('.sv-sidebar-cart-count').text(data.count || 0);
                this.$('.sv-sidebar-cart-total').html(data.total || '$0.00');
            }
        } catch (e) {
            $loading.addClass('d-none');
            $list.html('<div class="text-center py-5"><p style="color:var(--sv-muted,#9b8f85);">Error loading cart.</p></div>');
        }
    },
    /**
     * Closes the shopping cart sidebar.
     */
    _onCloseCart: function () {
        this.$('#savora_cart_sidebar, #restaurant_cart_backdrop').removeClass('open');
        document.body.style.overflow = '';
    },
    /**
     * Initializes scroll-based reveal animations using IntersectionObserver.
     */
    _initScrollReveal: function () {
        const els = document.querySelectorAll('.sv-reveal');
        if (!els.length || !('IntersectionObserver' in window)) return;
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => { if (entry.isIntersecting) entry.target.classList.add('visible'); });
        }, { threshold: 0.12 });
        els.forEach(el => observer.observe(el));
    },
    /**
     * Initializes sidebar accordions by setting default targets to open.
     */
    _initSidebarAccordions: function () {
        this.$('.rs-section-btn').each(function() {
            const target = $('#' + $(this).data('rs-target'));
            if (target.length) { target.addClass('rs-open'); $(this).addClass('rs-open'); }
        });
    },
    /**
     * Toggles the visibility of a sidebar accordion section.
     * @param {Event} ev
     */
    _onSidebarAccordionClick: function (ev) {
        const target = this.$('#' + $(ev.currentTarget).data('rs-target'));
        target.toggleClass('rs-open'); $(ev.currentTarget).toggleClass('rs-open');
    },
    /**
     * Animates numeric counters when they become visible on screen.
     */
    _initCounters: function () {
        this.$('.sv-num').each(function() {
            const $el = $(this);
            const target = parseInt($el.text().replace(/[^0-9]/g, ''), 10);
            if (isNaN(target)) return;
            const observer = new IntersectionObserver((entries) => {
                if (entries[0].isIntersecting) {
                    $({ c: 0 }).animate({ c: target }, { duration: 1200, step: function() { $el.text(Math.floor(this.c)); } });
                    observer.disconnect();
                }
            }, { threshold: 0.5 });
            observer.observe(this);
        });
    },
    /**
     * Handles smooth scrolling for internal anchor links.
     * @param {Event} ev
     */
    _onSmoothScroll: function (ev) {
        const href = $(ev.currentTarget).attr('href');
        if (!href || href === '#' || !href.startsWith('#')) return;
        try {
            const $target = this.$(href);
            if ($target.length) { ev.preventDefault(); $('html, body').animate({ scrollTop: $target.offset().top - 90 }, 600); }
        } catch (err) {
            // Ignore invalid selector errors
        }
    },
    /**
     * Reveals hidden reviews and plays an animation.
     * @param {Event} ev
     */
    _onSeeAllReviews: function (ev) {
        $(ev.currentTarget).fadeOut();
        this.$('.r-hidden').removeClass('r-hidden').addClass('sv-animate-up');
    },
    /**
     * Initializes the custom lightbox for the gallery.
     */
    _initGalleryLightbox: function () {
        const $lightbox = this.$('#sv_gallery_lightbox');
        if (!$lightbox.length) return;
        this.$('.sv-gallery-item').on('click', (ev) => {
            this.$('#sv_lightbox_img').attr('src', $(ev.currentTarget).find('img').attr('src'));
            $lightbox.addClass('sv-lb-open');
            document.body.style.overflow = 'hidden';
        });
        this.$('#sv_lightbox_close').on('click', () => { $lightbox.removeClass('sv-lb-open'); document.body.style.overflow = ''; });
    },
    /* ─── Reservation Logic ─── */
    /**
     * Returns a Date object representing today at midnight.
     * @returns {Date}
     */
    _getToday: function () {
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        return today;
    },
    /**
     * Checks if a given date is in the past.
     * @param {Date} date
     * @returns {boolean}
     */
    _isPastDate: function (date) {
        return date.getTime() < this._getToday().getTime();
    },
    /**
     * Renders the custom reservation calendar for the current view date.
     */
    _renderCalendar: function () {
        const monthNames = ["JANUARY", "FEBRUARY", "MARCH", "APRIL", "MAY", "JUNE", "JULY", "AUGUST", "SEPTEMBER", "OCTOBER", "NOVEMBER", "DECEMBER"];
        const month = this.currentViewDate.getMonth();
        const year = this.currentViewDate.getFullYear();
        const today = this._getToday();
        this.$('#calMonthYear').text(monthNames[month] + " " + year);
        const $grid = this.$('.sv-cal-grid');
        if (!$grid.length) return;
        $grid.empty();
        const firstDay = new Date(year, month, 1).getDay();
        const daysInMonth = new Date(year, month + 1, 0).getDate();
        const prevMonthLastDay = new Date(year, month, 0).getDate();
        for (let i = firstDay - 1; i >= 0; i--) {
            $grid.append($('<div class="sv-cal-day muted">').text(prevMonthLastDay - i));
        }
        for (let i = 1; i <= daysInMonth; i++) {
            const cellDate = new Date(year, month, i);
            let cls = 'sv-cal-day';
            if (this.selectedDate.getDate() === i && this.selectedDate.getMonth() === month && this.selectedDate.getFullYear() === year) cls += ' active';
            if (this._isPastDate(cellDate)) cls += ' muted';
            const $day = $('<div class="'+cls+'">').text(i);
            if (cls.includes('active')) $day.css('color', '#1b0f08');
            $grid.append($day);
        }
        for (let i = 1; i <= (42 - (firstDay + daysInMonth)); i++) {
            $grid.append($('<div class="sv-cal-day muted">').text(i));
        }
        this._updateSlots();
    },
    /**
     * Navigates the reservation calendar to the previous month.
     */
    _onPrevMonth: function () {
        const today = this._getToday();
        const prevMonth = new Date(this.currentViewDate);
        prevMonth.setDate(1);
        prevMonth.setMonth(prevMonth.getMonth() - 1);
        if (prevMonth.getFullYear() < today.getFullYear() || (prevMonth.getFullYear() === today.getFullYear() && prevMonth.getMonth() < today.getMonth())) {
            return;
        }
        this.currentViewDate = prevMonth;
        this._renderCalendar();
    },
    /**
     * Navigates the reservation calendar to the next month.
     */
    _onNextMonth: function () {
        const nextMonth = new Date(this.currentViewDate);
        nextMonth.setDate(1);
        nextMonth.setMonth(nextMonth.getMonth() + 1);
        this.currentViewDate = nextMonth;
        this._renderCalendar();
    },
    /**
     * Handles step selection (party size) in the reservation process.
     * @param {Event} ev
     */
    _onSelectStep: function (ev) { this.$('.sv-res-step-btn').removeClass('active'); $(ev.currentTarget).addClass('active'); this._updateReviewData(); },
    /**
     * Handles day selection on the reservation calendar.
     * @param {Event} ev
     */
    _onSelectDay: function (ev) {
        if ($(ev.currentTarget).hasClass('muted')) return;
        this.selectedDate = new Date(this.currentViewDate);
        this.selectedDate.setDate(parseInt($(ev.currentTarget).text().trim()));
        this.$('.sv-cal-day').removeClass('active');
        $(ev.currentTarget).addClass('active');
        this._updateSlots();
    },
    /**
     * Fetches and renders available time slots for the selected date.
     * @async
     */
    _updateSlots: async function () {
        const dateVal = this.selectedDate.getFullYear() + "-" + (this.selectedDate.getMonth() + 1).toString().padStart(2, '0') + "-" + this.selectedDate.getDate().toString().padStart(2, '0');
        try {
            const data = await jsonrpc('/reservations/get_slots', { date_str: dateVal });
            const $times = this.$('.sv-res-times');
            if (!$times.length) return;
            $times.empty();
            if (data && data.available_times && data.available_times.length) {
                data.available_times.forEach((t, i) => {
                    $times.append($('<div class="sv-res-time '+(i===0?'active':'')+'">').text(t));
                });
            } else {
                $times.append($('<p class="text-muted p-3" style="grid-column: 1 / -1; font-size:12px;">').text('No available slots.'));
            }
            this._updateReviewData();
        } catch (e) {}
    },
    /**
     * Handles time slot selection in the reservation process.
     * @param {Event} ev
     */
    _onSelectTime: function (ev) { this.$('.sv-res-time').removeClass('active'); $(ev.currentTarget).addClass('active'); this._updateReviewData(); },
    /**
     * Transitions from reservation Step 1 to Step 2.
     */
    _onToStep2: function () { if (!this.$('.sv-res-time.active').length) return alert("Select a time."); this.$('#reserveStep1').hide(); this.$('#reserveStep2').show(); this._updateReviewData(); },
    /**
     * Transitions back from reservation Step 2 to Step 1.
     */
    _onBackToStep1: function () { this.$('#reserveStep2').hide(); this.$('#reserveStep1').show(); },
    /**
     * Transitions from reservation Step 2 to Step 3.
     */
    _onToStep3: function () { if (!this.$('#resFirstName').val() || !this.$('#resEmail').val()) return alert("Fill required fields."); this._updateReviewData(); this.$('#reserveStep2').hide(); this.$('#reserveStep3').show(); },
    /**
     * Transitions back from reservation Step 3 to Step 2.
     */
    _onBackToStep2: function () { this.$('#reserveStep3').hide(); this.$('#reserveStep2').show(); },
    /**
     * Submits the reservation data and moves to the final confirmation step.
     * @async
     */
    _onToStep4: async function () {
        const dateVal = this.selectedDate.getFullYear() + "-" + (this.selectedDate.getMonth() + 1).toString().padStart(2, '0') + "-" + this.selectedDate.getDate().toString().padStart(2, '0');
        const data = {
            name: this.$('#resFirstName').val() + " " + (this.$('#resLastName').val() || ""),
            email: this.$('#resEmail').val(), phone: this.$('#resPhone').val(),
            date: dateVal, time: this.$('.sv-res-time.active').text().trim(),
            party_size: this.$('.sv-res-step-btn.active').text().trim() || '2',
            notes: this.$('#resNotes').val(),
        };
        try {
            const res = await jsonrpc('/reservations/submit', data);
            if (res && res.error) alert("Error: " + res.error);
            else { this.$('#reserveStep3').hide(); this.$('#reserveStep4').show(); }
        } catch (e) { alert("An error occurred."); }
    },
    /**
     * Updates the summary information in the reservation review step.
     */
    _updateReviewData: function () {
        const monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
        const fullDate = monthNames[this.selectedDate.getMonth()] + " " + this.selectedDate.getDate() + ", " + this.selectedDate.getFullYear();
        const guests = this.$('.sv-res-step-btn.active').text() || '2';
        this.$('#reviewDateVal, #confirmDateVal').text(fullDate);
        this.$('#reviewTimeVal, #confirmTimeVal').text(this.$('.sv-res-time.active').text() || '7:30 PM');
        this.$('#reviewGuestsVal, #confirmGuestsVal').text(guests + " Guests");
        this.$('#reviewNameVal').text(this.$('#resFirstName').val() + " " + (this.$('#resLastName').val() || ""));
        this.$('#reviewEmailVal').text(this.$('#resEmail').val());
        this.$('#reviewPhoneVal').text(this.$('#resPhone').val());
        this.$('#reviewNotesVal').text(this.$('#resNotes').val() || 'None');
    },
});

publicWidget.registry.SavoraTheme = SavoraTheme;

export default SavoraTheme;
