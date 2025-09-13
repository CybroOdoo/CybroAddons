odoo.define('pos_access_right_hr.ProductScreen', function (require) {
    'use strict';

    const ProductScreen = require('point_of_sale.ProductScreen');
    const Registries = require('point_of_sale.Registries');

    const PosAccessRightHrProductScreen = (ProductScreen) =>
        class extends ProductScreen {
            constructor() {
                super(...arguments);
            }

            async _updateSelectedOrderline(event) {
                const user = this.env.pos.get_cashier()
                if ((event.detail.key === "Backspace" || event.detail.key === "Delete" ) && user.disable_remove_button){
                    return;
                }
                if (/^[0-9]$/.test(event.detail.key) && user?.disable_numpad) {
                    return;
                }
                else if (event.detail.key === '-' && user?.disable_plus_minus) {
                    return; // Block + key
                }
                else if (event.detail.key === '+' && user?.disable_plus_minus) {
                    return; // Block + key
                }
                return super._updateSelectedOrderline(...arguments);
            }

        };

    Registries.Component.extend(ProductScreen, PosAccessRightHrProductScreen);
    return ProductScreen;
});
