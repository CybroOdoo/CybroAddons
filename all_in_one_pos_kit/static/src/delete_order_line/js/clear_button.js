odoo.define('all_in_one_pos_kit.DeleteOrderLinesAll', function(require) {
    'use strict';
    const PosComponent = require('point_of_sale.PosComponent');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const {useListener} = require("@web/core/utils/hooks");
    const Registries = require('point_of_sale.Registries');
    class OrderLineClearALL extends PosComponent { //Represents a custom control button for clearing all orders in the Point of Sale.
        setup() { //Super setup for the component.
            super.setup();
            useListener('click', this.onClick);
        }
        async onClick() { //Handles the click event when the button is clicked.
            const {
                confirmed
            } = await this.showPopup("ConfirmPopup", {
                title: this.env._t('Clear Orders?'),
                body: this.env._t('Are you sure you want to delete all orders from the cart?'),
            });
            if (confirmed) {
                var order = this.env.pos.get_order();
                order.get_orderlines().filter(line => line.get_product())
                    .forEach(line => order.remove_orderline(line));
            }
        }
    }
    OrderLineClearALL.template = 'OrderLineClearALL';
    ProductScreen.addControlButton({ // Add the control button to the ProductScreen component
        component: OrderLineClearALL,
        condition: function() {
            return this.env.pos;
        },
    });
    Registries.Component.add(OrderLineClearALL);
    return OrderLineClearALL;
});
