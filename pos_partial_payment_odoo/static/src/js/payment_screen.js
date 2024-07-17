odoo.define('pos_button.CustomButtonPaymentScreen', function(require) {
    'use strict';
    const { Gui } = require('point_of_sale.Gui');
    const PosComponent = require('point_of_sale.PosComponent');
    const { identifyError } = require('point_of_sale.utils');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const { useListener } = require("@web/core/utils/hooks");
    const Registries = require('point_of_sale.Registries');
    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const Chrome = require('point_of_sale.Chrome');
    const { useRef } = owl.hooks;
    // Define the PartialPaymentButtonPaymentScreen class
    const PartialPaymentButtonPaymentScreen = (PaymentScreen) =>
        class extends PaymentScreen {
            setup() {
                super.setup();
                this.root = useRef('PartialPayment');
            }
            //Partial Payment Button Functionality
            PartialPaymentButton() {
                if (this.currentOrder.partial_payment === false) {
                    this.currentOrder.partial_payment = true;
                    var validate = this.root.el
                    $(validate).addClass('highlight');
                } else {
                    this.currentOrder.partial_payment = false;
                    var validate = this.root.el
                    $(validate).removeClass('highlight');
                }
            }
            //Validate Payment Button Functionality
            async validateOrder(isForceValidate) {
                if (!this.currentOrder.partial_payment) {
                    await super.validateOrder(isForceValidate);
                } else {
                    if(this.currentOrder.get_client()){
                        if (this.currentOrder.get_client().prevent_partial_payment) {
                            this.showPopup('ErrorPopup', {
                                title: this.env._t('Partial Payment Not Allowed'),
                                body: this.env._t(
                                    'The Customer is not allowed to make Partial Payments.'
                                ),
                            });
                            return false;
                        };
                        //If Invoice not Selected Show Error
                        if (!this.currentOrder.to_invoice) {
                            this.showPopup('ErrorPopup', {
                                title: this.env._t('Cannot Validate This Order'),
                                body: this.env._t(
                                    'You need to Set Invoice for Validating Partial Payments'
                                ),
                            });
                            return false;
                        };
                        //If amount is fully paid show error
                        if (!this.currentOrder.get_due()) {
                            this.showPopup('ErrorPopup', {
                                title: this.env._t('Cannot Validate This Order'),
                                body: this.env._t(
                                    'The Amount is Fully Paid Disable Partial Payment to Validate this Order'
                                ),
                            });
                            return false;
                        };
                        this.currentOrder.is_partial_payment = true
                        this._isOrderValid(isForceValidate)
                        await this._finalizeValidation();
                    }else{
                        this.showPopup('ErrorPopup', {
                                title: this.env._t('Choose Any Customer'),
                                body: this.env._t(
                                    'Choose a customer for making partial payments.'
                                ),
                            });
                            return false;
                    }
                    await super.validateOrder(isForceValidate);
                }

            }
        };
    Registries.Component.extend(PaymentScreen, PartialPaymentButtonPaymentScreen);
    return PartialPaymentButtonPaymentScreen;
});
