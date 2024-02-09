odoo.define('point_of_sale.customer', function (require) {
    const ProductScreen = require('point_of_sale.ProductScreen');
    const { useListener } = require("@web/core/utils/hooks");
    const Registries = require('point_of_sale.Registries');
    const { _lt } = require('@web/core/l10n/translation');
    const CustomerButtons = (ProductScreen) =>
        class extends ProductScreen {
            /*Here, the ProductScreen has been extended, and some features have been overridden.*/
            setup() {
                super.setup();
                useListener('new-payment-line', this.newPaymentLine);
                useListener('confirm-order', this.confirmOrder);
                useListener('select-line', this._selectLine);
            }
            customerdetails() {
                this.onClickPartner();
            }
            confirmOrder() {
                /* When performing validation, this function checks the
                requirements and displays an error message if any are reduced.*/
                var paymentline = this.currentOrder.paymentlines.length
                var partner = this.currentOrder.partner
                var orderlines = this.currentOrder.orderlines.length
                if (orderlines == 0) {
                    this.showPopup('ErrorPopup', {
                        title: this.env._t('Error'),
                        body: this.env._t('Cart is empty.'),
                    });
                }
                else if (partner == null) {
                    this.showPopup('ErrorPopup', {
                        title: this.env._t('Error'),
                        body: this.env._t('Select a Customer.'),
                    });
                }
                else if (paymentline == 0) {
                    this.showPopup('ErrorPopup', {
                        title: this.env._t('Error'),
                        body: this.env._t('Select a Payment Method'),
                    });
                }
                else {
                    this.showPopup("ConfirmationPopup", {
                        title: _lt('Confirmation'),
                        confirmText: _lt('Confirm'),
                        cancelText: this.env._t('Cancel'),
                    });
                }
            }
            orderDone() {
                this.env.pos.removeOrder(this.currentOrder);
                this.env.pos.add_new_order();
                const { name, props } = this.nextScreen;
                this.showScreen(name, props);
                if (this.env.pos.config.iface_customer_facing_display) {
                    this.env.pos.send_current_order_to_customer_facing_display();
                }
            }
            newPaymentLine({ detail: paymentMethod }) {
                let result = this.currentOrder.add_paymentline(paymentMethod);
                if (result) {
                    return true;
                }
                else {
                    return false;
                }
            }
            get paymentLines() {
                return this.env.pos.get_order().get_paymentlines();
            }
            get_partner() {
                return this.partner;
            }
            set_partner(partner) {
                this.partner = this.env.pos.selectedPartner[4];
            }
            get nextScreen() {
                return { name: 'ProductScreen' };
            }
            _selectLine(event) {
                this.env.pos.selectedOrder.select_orderline(event.detail.orderline);
            }
            toggleIsToInvoice() {
                // click_invoice
                this.currentOrder.set_to_invoice(!this.currentOrder.is_to_invoice());
                this.render(true);
            }

        }
    Registries.Component.extend(ProductScreen, CustomerButtons);
    return CustomerButtons;
});