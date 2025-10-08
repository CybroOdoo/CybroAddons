// Extends the ProductScreen component in the Point of Sale to add the ability to magnify a product's image.
odoo.define('all_in_one_pos_kit.ProductScreen', function (require) {
    "use strict";
    const { useListener } = require("@web/core/utils/hooks");
    var Registries = require('point_of_sale.Registries');
    const ProductScreen = require('point_of_sale.ProductScreen');
    var core = require('web.core');
    var _t = core._t;
    const MagnifyProduct = ProductScreen => class extends ProductScreen {
        //Sets up the component and adds the click listener for magnifying a product.
        setup() {
        super.setup();
            useListener('click-magnify-product', this._clickMagnifyProduct);
            this.magnifyProduct = false;
        }
        // Handles the click event to magnify a product's image.
        async _clickMagnifyProduct(event) {
            this.magnifyProduct = true;
            const { confirmed } = await this.showPopup('MagnifyProductPopup', {
                title: this.env._t(event.detail.display_name),
                body: this.env._t(event.detail),
            });
            this.magnifyProduct = false;
        }
        // Handles the click event for a product.If the magnifyProduct flag is set to true, returns false to prevent the default behavior.
        async _clickProduct(event) {
            if (this.magnifyProduct === true) {
                return false;
            }
            super._clickProduct(event);
        }
    }
    // Extend the ProductScreen component with the MagnifyProduct component
    Registries.Component.extend(ProductScreen, MagnifyProduct);
    return MagnifyProduct;
});
