/** @odoo-module **/

import Registries from 'point_of_sale.Registries';
import ReceiptScreen from 'point_of_sale.ReceiptScreen';

const RestrictReceiptScreen = (ReceiptScreen) => {
    class RestrictReceiptScreen extends ReceiptScreen {
        async orderDone() {
            this.env.pos.get_order().orderlines.forEach(element => {
                element.product.setQty(element.quantity);
            });
            await super.orderDone();
        }
    }
    return RestrictReceiptScreen;
};
Registries.Component.extend(ReceiptScreen, RestrictReceiptScreen);

