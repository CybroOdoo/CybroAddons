odoo.define('pos_kitchen_screen_odoo.ReceiptScreen', function(require) {
    'use strict';

    const ReceiptScreen = require('point_of_sale.ReceiptScreen');
    const Registries = require('point_of_sale.Registries');

    const KitchenReceipt = ReceiptScreen =>
        class extends ReceiptScreen {
        //@Override the method to set the order count in the pos session
        orderDone() {
                this.env.pos.removeOrder(this.currentOrder);
                this.env.pos.add_new_order();
                const { name, props } = this.nextScreen;
                this.showScreen(name, props);
                if (this.env.pos.config.iface_customer_facing_display) {
                    this.env.pos.send_current_order_to_customer_facing_display();
                }
            }
        };
    Registries.Component.extend(ReceiptScreen, KitchenReceipt);
    return ReceiptScreen;
});
