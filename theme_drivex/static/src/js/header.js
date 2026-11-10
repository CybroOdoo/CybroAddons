/** @odoo-module **/

import animations from "@website/js/content/snippets.animation";
import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.headerDrivex = animations.Animation.extend({
    selector: '.drivexHeader',
    effects: [{
        startEvents: 'scroll',
        update: '_onScroll',
    }],
    _onScroll: function (scroll) {

        this.el.classList.toggle("scrolled", scroll > 60);
    },
});