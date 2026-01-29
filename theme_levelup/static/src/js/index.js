odoo.define('theme_levelup.index', function (require) {
    'use strict';
    var publicWidget = require('web.public.widget');
    var header;
    var nav;
    var pos;
    publicWidget.registry.ThemeIndex = publicWidget.Widget.extend({
        selector: '#wrapwrap',
        events: {
            'wheel main': '_handleScroll',
        },
        /* Start function fetching the classes */
        start: function () {
           header = this.$el.find(".header_modern_light");
           nav = this.$el.find('.navigation');
           pos = header.position();
        },
        /*  Function for website header scroll  */
        _handleScroll: function () {
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
    });
});
