odoo.define('pos_access_right_hr.ProductScreenAccessRight', function(require) {
    'use strict';
    const ProductScreen = require('point_of_sale.ProductScreen');
    const Registries = require('point_of_sale.Registries');
    const ProductScreenAccessRight= (ProductScreen) => class extends ProductScreen{
        /**
        * method to check the access of the cashier to use Delete and Backspace in ProductScreen
        */
        check_remove_access() {
            if (this.env.pos.config.module_pos_hr) {
                const cashierId = this.env.pos.get_cashier().id;
                const sessionAccess = this.env.pos.session_access.find(access => access.id === cashierId);
                return sessionAccess ? sessionAccess.disable_remove_button : false;
            } else {
                return false;
            }
        }
        /**
        * Override the method for disabling the usage of Delete and Backspace keys based on the access set for the cashier
        */
        async _updateSelectedOrderline(event) {
            if ((event.detail.key === "Backspace" || event.detail.key === "Delete" ) && this.check_remove_access()){
                return;
            }
            return super._updateSelectedOrderline(...arguments);
        }
    }
      Registries.Component.extend(ProductScreen, ProductScreenAccessRight);
      return ProductScreen;
});
