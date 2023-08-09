odoo.define('pos_numpad_show_hide.show_hide_numpad', function (require) {
    "use strict";
    const ProductScreen = require('point_of_sale.ProductScreen');
    const { useListener } = require('web.custom_hooks');
    const Registries = require("point_of_sale.Registries");

// Extending pos product screen for adding toggle icon
    const ProductScreenHideShowNumpad = (ProductScreen) =>
        class extends ProductScreen {
//        Function for view and hide pos numpad on clicking the toggle icon
        NumpadVisibility() {
            $('.pads').slideToggle('slow', function() {
                $('.numpad-toggle').toggleClass('fa-eye fa-eye-slash');
            });
            }
         }
    Registries.Component.extend(ProductScreen, ProductScreenHideShowNumpad);
    return ProductScreen;
});