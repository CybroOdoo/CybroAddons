odoo.define('product_exchange_pos_sys.Orders', function(require) {
    'use strict';
    const PosComponent = require('point_of_sale.PosComponent');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const { useListener } = require('web.custom_hooks');
    const Registries = require('point_of_sale.Registries');

    class AllOrders extends PosComponent {
        setup() {
            super.setup();
            useListener('click', this.onClick);
        }
//        Adding the button All order's
        onClick() {
            this.showScreen('CustomOrdrScreen', {
                orders: this.env.pos.pos_orders,
                pos: this.env.pos
            });
        }
    }
    AllOrders.template = 'AllOrders';
    ProductScreen.addControlButton({
        component: AllOrders,
        condition: function() {
            return true;
        },
    });
    Registries.Component.add(AllOrders);
    return AllOrders;
});
