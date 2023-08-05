odoo.define('pos_all_orders.all_order_screen', function(require) {
    'use strict';
    const PosComponent = require('point_of_sale.PosComponent');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const Registries = require('point_of_sale.Registries');

    class CustomALLOrdrScreen extends PosComponent {
    setup() {
        super.setup();
        this.state = {
            order: this.props.orders
        };
    }
    /**
     * For showing the Product screen
     */
    back() {
        this.showScreen('ProductScreen');
    }
};
CustomALLOrdrScreen.template = 'CustomALLOrdrScreen';
Registries.Component.add(CustomALLOrdrScreen);
return CustomALLOrdrScreen;
});