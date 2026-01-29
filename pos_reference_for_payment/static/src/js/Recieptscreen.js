/** @odoo-module **/
const ReceiptScreen = require('point_of_sale.ReceiptScreen');
const Registries = require('point_of_sale.Registries');
const ExtendsReceiptScreen = (ReceiptScreen) => class extends ReceiptScreen {
    async orderDone() {
        await super.orderDone(...arguments);
        if (this.env.pos.user_payment_reference && this.env.pos.user_payment_reference.length > 0) {
            const lastRef = this.env.pos.user_payment_reference[this.env.pos.user_payment_reference.length - 1];
            if (lastRef) {
                lastRef.user_payment_reference = false;
            }
        }
    }
};
Registries.Component.extend(ReceiptScreen, ExtendsReceiptScreen);
return ExtendsReceiptScreen;