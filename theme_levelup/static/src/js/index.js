/** @odoo-module */
import PublicWidget from "@web/legacy/js/public/public_widget"

var header
var nav
var pos

export const themeIndex = PublicWidget.Widget.extend({
    selector: "#wrapwrap",
    events: {
        'wheel main': '_handleScroll',
    },
    /* Start function fetching the classes */
    start() {
       header = this.$el.find(".header_modern_light")
       nav = this.$el.find('.navigation')
       pos = header.position()
    },
    /*  Function for website header scroll  */
    _handleScroll() {
        var windowpos = $('#wrapwrap').scrollTop();
        if (windowpos >= pos.top & windowpos >= 100) {
            nav.addClass("fadeInDown");
            nav.addClass("bg_white");
            nav.addClass("b_shadow");
        } else {
            nav.removeClass("fadeInDown");
            nav.removeClass("bg_white");
            nav.removeClass("b_shadow");
        }
    },
})

PublicWidget.registry.themeIndex = themeIndex
