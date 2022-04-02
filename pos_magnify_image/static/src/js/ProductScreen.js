odoo.define('pos_magnify_image.ProductScreen', function (require) {
    "use strict";

    const { useListener } = require('web.custom_hooks');
    const Registries = require('point_of_sale.Registries');
    const ProductScreen = require('point_of_sale.ProductScreen');
    var core = require('web.core');
    var _t = core._t;

    const MagnifyProduct = ProductScreen =>
        class extends ProductScreen {
            constructor() {
                super(...arguments);
                useListener('click-magnify-product', this._clickMagnifyProduct);
                this.magnifyProduct = false;
            }
            async _clickMagnifyProduct(event) {
                this.magnifyProduct = true;
                const { confirmed } = await this.showPopup('MagnifyProductPopup', {
                    title: this.env._t(event.detail.display_name),
                    body: this.env._t(event.detail),
                });
                this.magnifyProduct = false;
            }
            async _clickProduct(event) {
                if (this.magnifyProduct == true) {
                    return false;
                }
                super._clickProduct(event);
            }
        }
    Registries.Component.extend(ProductScreen, MagnifyProduct);
    return MagnifyProduct;
});