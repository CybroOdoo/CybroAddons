odoo.define('all_in_one_pos_kit.show_hide_numpad', function (require) {
    "use strict";
    const ProductScreen = require('point_of_sale.ProductScreen');
    const { patch } = require('web.utils');
    //Patch the ProductScreen component to add a method for showing or hiding the numpad.
    patch(ProductScreen.prototype, 'hide_show_numpad', {
        NumpadVisibility(ev) {
             $(ev.target).parents().find('.pads').slideToggle('slow', function() {
                $(ev.target).parents().find('.numpad-toggle').toggleClass('fa-eye fa-eye-slash');
            });
        }
    })
});
