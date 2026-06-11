/** @odoo-module **/
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
