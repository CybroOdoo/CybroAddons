odoo.define('all_in_one_pos_kit.show_hide_numpad', function (require) {
    "use strict";
    const ProductScreen = require('point_of_sale.ProductScreen');
    const { patch } = require('web.utils');
    patch(ProductScreen.prototype, 'hide_show_numpad', {
        NumpadVisibility() {
            $('.pads').slideToggle('slow', function() {
                $('.numpad-toggle').toggleClass('fa-eye fa-eye-slash');
            });
        }
    })
});
