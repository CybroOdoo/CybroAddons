odoo.define('simplified_pos.customer', function(require) {
    const ProductScreen = require('point_of_sale.ProductScreen');
    const {
        useListener
    } = require('web.custom_hooks');
    const ajax = require('web.ajax');
    const Registries = require('point_of_sale.Registries');
    const {
        _lt
    } = require('@web/core/l10n/translation');
    const CustomerButtons = (ProductScreen) =>
        class extends ProductScreen {
            /*Here, the ProductScreen has been extended, and some features have been overridden.*/
            setup() {
                super.setup();
                useListener('new-payment-line', this.newPaymentLine);
                useListener('confirm-order', this.confirmOrder);
                useListener('select-line', this._selectLine);
            }
            get changeText() {
                return this.env.pos.format_currency(this.currentOrder.get_change());
            }
            get totalDueText() {
                return this.env.pos.format_currency(
                    this.currentOrder.get_total_with_tax() + this.currentOrder.get_rounding_applied()
                );
            }
            get remainingText() {
                return this.env.pos.format_currency(
                    this.currentOrder.get_due() > 0 ? this.currentOrder.get_due() : 0
                );
            }
            get currentOrder() {
                return this.env.pos.get_order();
            }
            get_current_Order() {
                return this.env.pos.get_order().get_paymentlines()
            }
            confirmOrder() {
                /* When performing validation, this function checks the
                requirements and displays an error message if any are reduced.*/
                var paymentline = this.currentOrder.paymentlines.length
                var partner = this.currentOrder.get_client()
                var orderlines = this.currentOrder.orderlines.length
                if (orderlines == 0) {
                    this.showPopup('ErrorPopup', {
                        title: this.env._t('Error'),
                        body: this.env._t('Cart is empty.'),
                    });
                } else if (partner == null) {
                    this.showPopup('ErrorPopup', {
                        title: this.env._t('Error'),
                        body: this.env._t('Select a Customer.'),
                    });
                } else if (paymentline == 0) {
                    this.showPopup('ErrorPopup', {
                        title: this.env._t('Error'),
                        body: this.env._t('Select a Payment Method'),
                    });
                } else {
                    this.showPopup("ConfirmationPopup", {
                        title: _lt('Confirmation'),
                        confirmText: _lt('Confirm'),
                        cancelText: this.env._t('Cancel'),
                    });
                }
            }
            orderDone() {
                this.currentOrder.finalize();
                const {
                    name,
                    props
                } = this.nextScreen;
                this.showScreen(name, props);
                if (this.env.pos.config.iface_customer_facing_display) {
                    this.env.pos.send_current_order_to_customer_facing_display();
                }
            }
            newPaymentLine({
                detail: paymentMethod
            }) {
                let result = this.currentOrder.add_paymentline(paymentMethod);
                if (result) {
                    this.render(true)
                    return true;
                } else {
                    this.render(true)
                    return false;
                }
            }
            get_payment_methods() {
                return this.env.pos.payment_methods
            }
            get paymentLines() {
                return this.env.pos.get_order().get_paymentlines();
            }
            get nextScreen() {
                return {
                    name: 'ProductScreen'
                };
            }
            _selectLine(event) {
                this.currentOrder.select_orderline(event.detail.orderline);
            }
        }
    Registries.Component.extend(ProductScreen, CustomerButtons);
    return this;
});