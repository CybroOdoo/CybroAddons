odoo.define('pos_pro_cross_selling.product_addons', function (require) {
    "use strict";

    const Registries = require('point_of_sale.Registries');
    var rpc = require('web.rpc');
    const { Gui } = require('point_of_sale.Gui');
    const ProductScreen = require('point_of_sale.ProductScreen');
    // Class for pos products
    const PosProductAddons = ProductScreen => class extends ProductScreen {
        setup(){
            //Supering the setup
            super.setup();
        }
        async _clickProduct(event) {
            // Click Function for the products, It opens the pop up
            super._clickProduct(...arguments)
            const product = event.detail;
            var self = this;
            rpc.query({
                model: 'pos.cross.selling',
                method: 'get_cross_selling_products',
                args: [[],product.id],
            }).then(function (result) {
                if (result.length > 0) {
                    Gui.showPopup('CrossProducts', {
                        product: result
                    });
                }
            });
        }
    };
    Registries.Component.extend(ProductScreen, PosProductAddons);
    return ProductScreen;
});
