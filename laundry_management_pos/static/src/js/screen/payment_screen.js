/** @odoo-module **/
import PaymentScreen from 'point_of_sale.PaymentScreen';
import Registries from 'point_of_sale.Registries';
export const PosLoyaltyPaymentScreen = (PaymentScreen) =>
    class extends PaymentScreen {
        //@override
       async validateOrder(isForceValidate) {
       const order = this.currentOrder;
            const hasWashingType = order.get_orderlines().some(line => line.washingType);
            if (hasWashingType && !order.get_partner()) {
                const { confirmed } = await this.showPopup('ConfirmPopup', {
                    title: this.env._t('Please select the Customer'),
                    body: this.env._t(
                        'You need to select the customer for the order contains laundry products.'
                    ),
                });
                if (confirmed) {
                    this.selectPartner();
                }
                return false
            }
            await super.validateOrder(...arguments);
        }
    };
Registries.Component.extend(PaymentScreen, PosLoyaltyPaymentScreen);
