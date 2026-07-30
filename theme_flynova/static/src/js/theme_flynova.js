/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";
import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";

// Minimal no-op OWL component — satisfies the <owl-component name="theme_flynova.FlynovaTheme"/>
// mount-point in the layout. All DOM logic lives in the public widgets below.
export class FlynovaTheme extends Component {
    static template = "theme_flynova.FlynovaTheme";
}
registry.category("public_components").add("theme_flynova.FlynovaTheme", FlynovaTheme);

// ── Scroll header ─────────────────────────────────────────────────────────────
// selector: 'header#top'  →  this.el IS the header element.
// Toggles .active on this.el directly — no document.* queries needed.

const FlynovaScrollHeaderWidget = publicWidget.Widget.extend({
    selector: 'header#top',

    start() {
        // Apply immediately (synchronous) so the correct header background is
        // set before the first painted frame — avoids a transparent-to-white flicker.
        this._onScroll = () => this.el.classList.toggle('active', window.scrollY > 1);
        this._onScroll();
        window.addEventListener('scroll', this._onScroll, { passive: true });
        return this._super(...arguments);
    },

    destroy() {
        if (this._onScroll) window.removeEventListener('scroll', this._onScroll);
        this._super(...arguments);
    },
});

publicWidget.registry.FlynovaScrollHeaderWidget = FlynovaScrollHeaderWidget;

// ── Mobile menu ───────────────────────────────────────────────────────────────
// selector: '#wrapwrap'  →  public widgets attach from #wrapwrap by default, so a
// 'body' selector would never match; #wrapwrap reliably wraps the header/mobile-nav.
// events dict handles the three triggers; handler queries within this.el.

const FlynovaMobileMenuWidget = publicWidget.Widget.extend({
    selector: '#wrapwrap',
    events: {
        'click #menuBtn': '_onMenuToggle',
        'click #closeBtn': '_onMenuToggle',
        'click #overlay': '_onMenuToggle',
    },

    _onMenuToggle() {
        const nav = this.el.querySelector('#mobileNav');
        const overlay = this.el.querySelector('#overlay');
        if (!nav || !overlay) return;
        nav.classList.toggle('active');
        overlay.classList.toggle('active');
    },
});

publicWidget.registry.FlynovaMobileMenuWidget = FlynovaMobileMenuWidget;

// ── Active nav links ────────────────────────────────────────────────────────────
// selector: '#wrapwrap'  →  highlights the header/mobile nav link matching the current path.
// All lookups scoped to this.el — no document.* calls.

const FlynovaActiveNavLinksWidget = publicWidget.Widget.extend({
    selector: '#wrapwrap',

    start() {
        this._updateActiveNavLinks();
        return this._super(...arguments);
    },

    _updateActiveNavLinks() {
        const navLinks = this.el.querySelectorAll(
            'header#top .top_menu a.nav-link[href], #top_menu_collapse_mobile a.nav-link[href], .mobile-nav-links a[href]'
        );
        if (!navLinks.length) return;

        const normalizePath = (path) => {
            const cleanPath = path.split('?')[0].split('#')[0].replace(/\/+$/, '');
            return cleanPath || '/';
        };
        const currentPath = normalizePath(window.location.pathname);
        const aliases = new Map([
            ['/packages', '/tours'],
            ['/about', '/about-us'],
            ['/aboutus', '/about-us'],
        ]);
        const effectivePath = aliases.get(currentPath) || currentPath;
        const groupedPaths = {
            '/tours': ['/tours', '/tour', '/packages'],
            '/hotels': ['/hotels', '/hotel'],
            '/explore': ['/explore'],
            '/about-us': ['/about-us', '/about', '/aboutus'],
        };

        navLinks.forEach((link) => {
            const navItem = link.closest('.nav-item');
            link.classList.remove('active');
            if (navItem) navItem.classList.remove('active');

            const linkPath = normalizePath(new URL(link.href, window.location.origin).pathname);
            const effectiveLinkPath = aliases.get(linkPath) || linkPath;
            const matchesPath = effectivePath === effectiveLinkPath
                || (effectiveLinkPath !== '/' && effectivePath.startsWith(`${effectiveLinkPath}/`))
                || (groupedPaths[effectiveLinkPath] || []).some((path) => (
                    effectivePath === path || effectivePath.startsWith(`${path}/`)
                ));

            if (matchesPath) {
                link.classList.add('active');
                if (navItem) navItem.classList.add('active');
            }
        });
    },
});

publicWidget.registry.FlynovaActiveNavLinksWidget = FlynovaActiveNavLinksWidget;

// ── Carousel ──────────────────────────────────────────────────────────────────
// selector: '.flynova-carousel'  →  one widget instance per carousel; this.el IS the carousel root.
// All child lookups use this.el.querySelector — zero document.* calls.

const FlynovaCarouselWidget = publicWidget.Widget.extend({
    selector: '.flynova-carousel',
    events: {
        'click .flynova-carousel-control--prev': '_onPrevClick',
        'click .flynova-carousel-control--next': '_onNextClick',
        'mouseenter': '_onMouseEnter',
        'mouseleave': '_onMouseLeave',
        'focusin': '_onFocusIn',
        'focusout': '_onFocusOut',
        'touchstart': '_onTouchStart',
        'touchend': '_onTouchEnd',
    },

    start() {
        this._viewport = this.el.querySelector('.flynova-carousel-viewport');
        this._track = this.el.querySelector('.flynova-carousel-track');
        this._prevBtn = this.el.querySelector('.flynova-carousel-control--prev');
        this._nextBtn = this.el.querySelector('.flynova-carousel-control--next');
        this._controlsEnabled = this.el.dataset.carouselControls !== 'false';
        this._sourceSlides = Array.from(
            this._track ? this._track.querySelectorAll('.flynova-carousel-slide') : []
        );
        this._autoplayId = null;
        this._animations = new Map();
        this._timeouts = [];

        if (!this._viewport || !this._track || !this._sourceSlides.length) {
            return this._super(...arguments);
        }

        if (this._sourceSlides.length > 1) {
            this._sourceSlides.forEach((slide) => this._track.appendChild(slide.cloneNode(true)));
        }

        this._updateStaticState();

        this._onResize = () => {
            this._normalizePosition();
            this._updateStaticState();
        };
        window.addEventListener('resize', this._onResize, { passive: true });

        if (this.el.dataset.carouselAutoplay === 'true' && this._sourceSlides.length > 1) {
            this._startAutoplay();
        }

        return this._super(...arguments);
    },

    destroy() {
        this._stopAutoplay();
        if (this._onResize) window.removeEventListener('resize', this._onResize);
        this._timeouts.forEach((id) => window.clearTimeout(id));
        this._animations.forEach((id) => window.cancelAnimationFrame(id));
        this._super(...arguments);
    },

    _onPrevClick() { if (this._controlsEnabled) this._scrollByStep(-1); },
    _onNextClick() { if (this._controlsEnabled) this._scrollByStep(1); },
    _onMouseEnter() { this._stopAutoplay(); },
    _onMouseLeave() { this._startAutoplay(); },
    _onFocusIn() { this._stopAutoplay(); },
    _onFocusOut() { this._startAutoplay(); },
    _onTouchStart() { this._stopAutoplay(); },
    _onTouchEnd() { this._startAutoplay(); },

    _getStride() {
        const first = this._track.querySelector('.flynova-carousel-slide');
        if (!first) return this._viewport.clientWidth;
        const style = window.getComputedStyle(this._track);
        const gap = parseFloat(style.columnGap || style.gap || '0');
        return first.getBoundingClientRect().width + gap;
    },

    _getCycleWidth() {
        return this._getStride() * this._sourceSlides.length;
    },

    _updateStaticState() {
        const isStatic = this._sourceSlides.length <= 1;
        this.el.classList.toggle('is-static', isStatic);
        if (this._prevBtn) this._prevBtn.disabled = isStatic;
        if (this._nextBtn) this._nextBtn.disabled = isStatic;
    },

    _normalizePosition() {
        if (this._sourceSlides.length <= 1) return;
        const cycleWidth = this._getCycleWidth();
        const currentLeft = this._viewport.scrollLeft;
        if (currentLeft >= cycleWidth) {
            this._viewport.scrollLeft = currentLeft - cycleWidth;
        } else if (currentLeft < 0) {
            this._viewport.scrollLeft = currentLeft + cycleWidth;
        }
    },

    _scrollByStep(direction) {
        if (this._sourceSlides.length <= 1) return;
        const stride = this._getStride();
        const cycleWidth = this._getCycleWidth();
        if (direction < 0 && this._viewport.scrollLeft <= 1) this._viewport.scrollLeft = cycleWidth;
        this._animateScroll(this._viewport, this._viewport.scrollLeft + stride * direction, 240);
        const id = window.setTimeout(() => {
            this._timeouts = this._timeouts.filter((t) => t !== id);
            if (direction > 0 && this._viewport.scrollLeft >= cycleWidth - stride * 0.35) {
                this._viewport.scrollLeft -= cycleWidth;
            } else if (direction < 0 && this._viewport.scrollLeft <= stride * 0.35) {
                this._viewport.scrollLeft += cycleWidth;
            }
        }, 250);
        this._timeouts.push(id);
    },

    _startAutoplay() {
        if (this._autoplayId || !this._sourceSlides || this._sourceSlides.length <= 1) return;
        const ms = parseInt(this.el.dataset.carouselInterval || '2200', 10);
        this._autoplayId = window.setInterval(() => this._scrollByStep(1), ms);
    },

    _stopAutoplay() {
        if (this._autoplayId) {
            window.clearInterval(this._autoplayId);
            this._autoplayId = null;
        }
    },

    _animateScroll(viewport, targetLeft, duration = 260) {
        const current = this._animations.get(viewport);
        if (current) window.cancelAnimationFrame(current);

        const startLeft = viewport.scrollLeft;
        const distance = targetLeft - startLeft;
        if (Math.abs(distance) < 1) {
            viewport.scrollLeft = targetLeft;
            return;
        }

        const startTime = performance.now();
        const easeOutCubic = (t) => 1 - Math.pow(1 - t, 3);

        const step = (now) => {
            const progress = Math.min((now - startTime) / duration, 1);
            viewport.scrollLeft = startLeft + distance * easeOutCubic(progress);
            if (progress < 1) {
                const animId = window.requestAnimationFrame(step);
                this._animations.set(viewport, animId);
            } else {
                this._animations.delete(viewport);
                viewport.scrollLeft = targetLeft;
            }
        };

        const animId = window.requestAnimationFrame(step);
        this._animations.set(viewport, animId);
    },
});

publicWidget.registry.FlynovaCarouselWidget = FlynovaCarouselWidget;

// ── Booking detail (counters, gallery, extra services, total) ──────────────────
// selector: '.top-section' — the tour/hotel detail templates wrap the gallery and
// booking panel in this container, so this.el covers every element the widget needs
// (#adult_qty_input, #hotel_total_price, etc.) — no document.* calls anywhere.

const FlynovaBookingWidget = publicWidget.Widget.extend({
    selector: '.top-section',
    events: {
        'click .counter-btn': '_onCounterClick',
        'click .booking-thumbnail': '_onThumbnailClick',
        'change .extra-service-checkbox': '_onExtraServiceChange',
    },

    start() {
        this._updateBookingTotal();
        return this._super(...arguments);
    },

    _onCounterClick(ev) {
        const btn = ev.target.closest('.counter-btn');
        if (!btn) return;
        const control = btn.closest('.counter-controls');
        if (!control) return;
        const delta = btn.classList.contains('minus') ? -1 : 1;
        this._stepCounter(control, delta);
    },

    _stepCounter(control, delta) {
        const type = control.dataset.type;
        const valueDisplay = control.querySelector('.counter-value');
        const hiddenInput = this.el.querySelector('#' + type + '_qty_input');
        if (!valueDisplay || !hiddenInput) return;
        const minimum = type === 'adult' ? 1 : 0;
        const parsed = parseInt(valueDisplay.textContent, 10);
        const current = Number.isNaN(parsed) ? minimum : parsed;
        const next = Math.max(minimum, current + delta);
        valueDisplay.textContent = next;
        hiddenInput.value = next;
        this._updateBookingTotal();
    },

    _onThumbnailClick(ev) {
        const thumb = ev.target.closest('.booking-thumbnail');
        if (!thumb) return;
        const img = thumb.querySelector('img');
        const mainImage = this.el.querySelector('#main_booking_image');
        if (!img || !mainImage) return;
        mainImage.src = img.src;
        this.el.querySelectorAll('.booking-thumbnail').forEach((t) => t.classList.remove('active'));
        thumb.classList.add('active');
    },

    _onExtraServiceChange() {
        this._updateBookingTotal();
    },

    _updateBookingTotal() {
        const totalEl =
            this.el.querySelector('#tour_total_price') ||
            this.el.querySelector('#hotel_total_price');
        if (!totalEl) return;

        const adultPrice = parseFloat(totalEl.dataset.adultPrice || '0');
        const childPrice = parseFloat(totalEl.dataset.childPrice || '0');
        const adultInput = this.el.querySelector('#adult_qty_input');
        const childInput = this.el.querySelector('#child_qty_input');
        const adultQty = parseInt((adultInput && adultInput.value) || '1', 10);
        const childQty = parseInt((childInput && childInput.value) || '0', 10);
        const totalGuests = adultQty + childQty;

        let total = adultQty * adultPrice + childQty * childPrice;
        this.el.querySelectorAll('.extra-service-checkbox').forEach((cb) => {
            if (cb.checked) total += parseFloat(cb.dataset.price || '0') * totalGuests;
        });

        totalEl.textContent = Math.round(total);
    },
});

publicWidget.registry.FlynovaBookingWidget = FlynovaBookingWidget;

// ── Payment buttons ───────────────────────────────────────────────────────────
// selector: '.payment-section'  →  this.el is the right-hand payment panel.
// Both #payment_method and .flynova-payment-back-btn are children of .payment-section,
// so this.el.querySelector covers everything — no document.* calls.

const FlynovaPaymentWidget = publicWidget.Widget.extend({
    selector: '.payment-section',

    start() {
        window.setTimeout(() => this._alignButtons(), 0);
        return this._super(...arguments);
    },

    destroy() {
        if (this._observer) this._observer.disconnect();
        this._super(...arguments);
    },

    _alignButtons() {
        const backBtn = this.el.querySelector('.flynova-payment-back-btn');
        if (!backBtn) return;

        const tryAlign = () => {
            const submitBtn = this.el.querySelector('button[name="o_payment_submit_button"]');
            if (submitBtn && backBtn.parentNode !== submitBtn.parentNode) {
                submitBtn.parentNode.insertBefore(backBtn, submitBtn);
                const wrapper = this.el.querySelector('.action-buttons');
                if (wrapper && !wrapper.children.length) wrapper.remove();
                return true;
            }
            return false;
        };

        if (tryAlign()) return;

        const paymentMethodEl = this.el.querySelector('#payment_method');
        if (paymentMethodEl) {
            this._observer = new MutationObserver((_mutations, obs) => {
                if (tryAlign()) obs.disconnect();
            });
            this._observer.observe(paymentMethodEl, { childList: true, subtree: true });
        }
    },
});

publicWidget.registry.FlynovaPaymentWidget = FlynovaPaymentWidget;

// ── Listing filter (tour/hotel/package sidebars) ────────────────────────────────
// selector: '.flynova-listing-filter'  →  this.el IS the filter <form>.
// Replaces the onchange="this.form.submit()" / oninput / inline <script> that
// used to live in the tour, hotel and event listing templates.

const FlynovaListingFilterWidget = publicWidget.Widget.extend({
    selector: '.flynova-listing-filter',
    events: {
        'change select': '_onSelectChange',
        'change input[type="checkbox"]': '_onCheckboxChange',
        'input input[type="range"]': '_onRangeInput',
        'change input[type="range"]': '_onRangeChange',
    },

    start() {
        const range = this.el.querySelector('input[type="range"][name="max_price"]');
        const display = this.el.querySelector('.flynova-price-display');
        if (range && display) {
            display.textContent = range.value;
        }
        return this._super(...arguments);
    },

    _onSelectChange() {
        this.el.submit();
    },

    _onRangeInput(ev) {
        const display = this.el.querySelector('.flynova-price-display');
        if (display) {
            display.textContent = ev.currentTarget.value;
        }
    },

    _onRangeChange() {
        this.el.submit();
    },

    _onCheckboxChange() {
        const action = this.el.getAttribute('action') || window.location.pathname;
        const url = new URL(window.location.origin + action);

        this.el.querySelectorAll('select[name]').forEach((sel) => {
            url.searchParams.set(sel.name, sel.value);
        });
        this.el.querySelectorAll('input[type="range"][name]').forEach((inp) => {
            url.searchParams.set(inp.name, inp.value);
        });

        const groups = {};
        this.el.querySelectorAll('input[type="checkbox"][name]:checked').forEach((cb) => {
            (groups[cb.name] = groups[cb.name] || []).push(cb.value);
        });
        Object.entries(groups).forEach(([name, vals]) => {
            url.searchParams.set(name, vals.join(','));
        });

        window.location.href = url.toString();
    },
});

publicWidget.registry.FlynovaListingFilterWidget = FlynovaListingFilterWidget;
