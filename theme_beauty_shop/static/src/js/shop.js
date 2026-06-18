/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

/**
 * Public widget for the Beauty Shop theme.
 * Manages global UI effects like scroll-to-top and hero banner pagination.
 */
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
     * Initializes scroll-dependent UI changes, such as showing the
     * "Back to Top" button and updating the body class for header styling.
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
     * Initializes the automatic pagination animation for the hero banner.
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
