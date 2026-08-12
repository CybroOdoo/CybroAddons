/** @odoo-module **/

import animations from "@website/js/content/snippets.animation";
import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.headerDrivex = animations.Animation.extend({
    selector: '.headerNav',
    effects: [{
        startEvents: 'scroll',
        update: '_onScroll',
    }],
    _onScroll: function (scroll) {
        if (scroll > 20) {
            this.el.classList.add('nav--scrolled');
        } else {
            this.el.classList.remove('nav--scrolled');
        }
    },
});
