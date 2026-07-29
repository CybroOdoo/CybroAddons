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
// Toggles .active on this.el directly and strips the inline transform Odoo
// injects on o_header_affixed (which overrides even !important CSS rules) —
// no document.* queries needed.

const FlynovaScrollHeaderWidget = publicWidget.Widget.extend({
    selector: 'header#top',

    start() {
        this._wrap = this.el.closest('#wrapwrap');

        this._getScrollTop = () => (
            window.scrollY
            || document.documentElement.scrollTop
            || document.body.scrollTop
            || (this._wrap && this._wrap.scrollTop)
            || 0
        );

        this._onScroll = () => {
            this.el.style.removeProperty('transform');
            this.el.style.removeProperty('right');
            this.el.classList.toggle('active', this._getScrollTop() > 1);
        };
        this._onPrepareScroll = (ev) => {
            if ((ev.deltaY || 0) > 0 || this._getScrollTop() > 1) {
                this.el.classList.add('active');
            }
        };

        this._onScroll();
        window.addEventListener('scroll', this._onScroll, { passive: true });
        window.addEventListener('wheel', this._onPrepareScroll, { passive: true });
        window.addEventListener('touchstart', this._onPrepareScroll, { passive: true });
        window.addEventListener('pageshow', this._onScroll);
        if (this._wrap) {
            this._wrap.addEventListener('scroll', this._onScroll, { passive: true });
        }

        // Odoo rewrites the header's inline style on affix/unaffix — watch it
        // and strip the transform/right properties every time it comes back.
        this._styleObserver = new MutationObserver(() => {
            if (this.el.style.transform || this.el.style.right) {
                this.el.style.removeProperty('transform');
                this.el.style.removeProperty('right');
            }
        });
        this._styleObserver.observe(this.el, { attributes: true, attributeFilter: ['style'] });

        return this._super(...arguments);
    },

    destroy() {
        window.removeEventListener('scroll', this._onScroll);
        window.removeEventListener('wheel', this._onPrepareScroll);
        window.removeEventListener('touchstart', this._onPrepareScroll);
        window.removeEventListener('pageshow', this._onScroll);
        if (this._wrap) {
            this._wrap.removeEventListener('scroll', this._onScroll);
        }
        if (this._styleObserver) {
            this._styleObserver.disconnect();
        }
        this._super(...arguments);
    },
});

publicWidget.registry.FlynovaScrollHeaderWidget = FlynovaScrollHeaderWidget;

// ── Mobile menu ───────────────────────────────────────────────────────────────
// selector: 'body'  →  this.el = body; all mobile-nav elements are children.
// events dict handles the three triggers; handler queries within this.el.

const FlynovaMobileMenuWidget = publicWidget.Widget.extend({
    selector: 'body',
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
    },

    start() {
        this._viewport = this.el.querySelector('.flynova-carousel-viewport');
        this._track = this.el.querySelector('.flynova-carousel-track');
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

        this._onResize = () => this._updateStaticState();
        window.addEventListener('resize', this._onResize, { passive: true });

        this._onTouchStart = () => this._stopAutoplay();
        this._onTouchEnd = () => this._startAutoplay();
        this.el.addEventListener('touchstart', this._onTouchStart, { passive: true });
        this.el.addEventListener('touchend', this._onTouchEnd, { passive: true });

        if (this.el.dataset.carouselAutoplay === 'true' && this._sourceSlides.length > 1) {
            this._startAutoplay();
        }

        return this._super(...arguments);
    },

    destroy() {
        this._stopAutoplay();
        if (this._onResize) window.removeEventListener('resize', this._onResize);
        if (this._onTouchStart) this.el.removeEventListener('touchstart', this._onTouchStart);
        if (this._onTouchEnd) this.el.removeEventListener('touchend', this._onTouchEnd);
        this._timeouts.forEach((id) => window.clearTimeout(id));
        this._animations.forEach((id) => window.cancelAnimationFrame(id));
        this._super(...arguments);
    },

    _onPrevClick() { this._scrollByStep(-1); },
    _onNextClick() { this._scrollByStep(1); },
    _onMouseEnter() { this._stopAutoplay(); },
    _onMouseLeave() { this._startAutoplay(); },
    _onFocusIn() { this._stopAutoplay(); },
    _onFocusOut() { this._startAutoplay(); },

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
        const prevBtn = this.el.querySelector('.flynova-carousel-control--prev');
        const nextBtn = this.el.querySelector('.flynova-carousel-control--next');
        if (prevBtn) prevBtn.disabled = isStatic;
        if (nextBtn) nextBtn.disabled = isStatic;
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

    _animateScroll(viewport, targetLeft, duration) {
        duration = duration === undefined ? 260 : duration;
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
// selector: '.flynova-booking-detail' — added to <div class="top-section"> in hotel/tour detail templates.
// this.el IS that container, so every child (#adult_qty_input, #hotel_total_price, etc.)
// is found via this.el.querySelector — no document.* calls anywhere in this widget.

const FlynovaBookingWidget = publicWidget.Widget.extend({
    selector: '.flynova-booking-detail',
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
        const current = parseInt(valueDisplay.textContent, 10);
        const next = Math.max(type === 'adult' ? 1 : 0, current + delta);
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
