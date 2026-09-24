/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.BeautyShop = publicWidget.Widget.extend({
    selector: '#wrapwrap',
    /**
     * @override
     */
    start: function () {
        this._super.apply(this, arguments);
        this._initScrollEffects();
        this._initHeroPagination();
    },
    /**
     * Initializes scroll-based effects, such as the "Back to Top" button visibility
     * and adding a 'scrolled' class to the body.
     *
     * @private
     */
    _initScrollEffects: function () {
        const btt = this.el.querySelector('#backToTop');
        window.addEventListener('scroll', () => {
            const y = window.scrollY;
            if (btt) {
                btt.classList.toggle('visible', y > 600);
            }
            document.body.classList.toggle('scrolled', y > 40);
        }, { passive: true });
        if (btt) {
            btt.addEventListener('click', (e) => {
                e.preventDefault();
                window.scrollTo({ top: 0, behavior: 'smooth' });
            });
        }
    },
    /**
     * Initializes the pagination dots for the hero section slider,
     * cycling through them at a fixed interval.
     *
     * @private
     */
    _initHeroPagination: function () {
        const dots = this.el.querySelectorAll('.hero-pagination .dot');
        if (dots.length) {
            let active = 0;
            setInterval(() => {
                dots[active].classList.remove('active');
                active = (active + 1) % dots.length;
                dots[active].classList.add('active');
            }, 4200);
        }
    }
});
